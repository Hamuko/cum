from bs4 import BeautifulSoup
from cum import config, exceptions, output
from cum.scrapers.base import BaseChapter, BaseSeries, download_pool
from functools import partial
from mimetypes import guess_type
from urllib.parse import urljoin, urlparse
import concurrent.futures
import re
import requests


class MangadexSeries(BaseSeries):
    """Scraper for mangadex.org.

    Some examples of chapter info used by Mangadex (matched with `name_re`):
        Vol. 2 Ch. 18 - Strange-flavored Ramen
        Ch. 7 - Read Online
        Vol. 01 Ch. 001-013 - Read Online
        Vol. 2 Ch. 8 v2 - Read Online
        Oneshot
    """
    url_re = re.compile(r'(?:https?://mangadex\.(?:org|com))?/manga/([0-9]+)')
    name_re = re.compile(r'Ch\. ?([A-Za-z0-9\.\-]*)(?: v[0-9]+)?(?: - (.*))')
    language_re = re.compile(r'/images/flags/')
    group_re = re.compile(r'/group/([0-9]+)')

    def __init__(self, url, **kwargs):
        super().__init__(url, **kwargs)
        self._get_page(self.url)
        self.chapters = self.get_chapters()
        # fetch paginated chapters
        while True:
            next_url = self._get_next_url()
            if not next_url:
                break
            self._get_page(next_url)
            self.chapters = self.get_chapters() + self.chapters

    def _get_page(self, url):
        r = requests.get(url)
        self.soup = BeautifulSoup(r.text, config.get().html_parser)

    def _get_next_url(self):
        pagination = self.soup.find('ul', class_='pagination')
        active_item = (pagination.find('li', class_='active')
                       if pagination else None)
        next_item = (active_item.find_next_sibling('li', class_='paging')
                     if active_item else None)
        next_link = next_item.find('a') if next_item else None
        next_url = next_link.get('href') if next_link else None
        return urljoin('https://mangadex.com', next_url) if next_url else None

    def get_chapters(self):
        links = self.soup.find_all('a')
        chapters = []

        manga_name = self.name
        for a in links:
            url = a.get('href')
            url_match = re.search(MangadexChapter.url_re, url) if url else None
            if not url_match:
                continue
            name = a.string
            if not name:
                print("no name for {}".format(url))
                continue
            name = name.strip()
            name_parts = re.search(self.name_re, name)
            chapter = name_parts.group(1) if name_parts else name
            title = name_parts.group(2) if name_parts else None
            title = None if title == 'Read Online' else title
            language = a.parent.parent.find('img', src=self.language_re)\
                                      .get('title')
            # TODO: Add an option to filter by language.
            if language != 'English':
                continue
            groups = [a.parent.parent.find('a', href=self.group_re).string]
            c = MangadexChapter(name=manga_name, alias=self.alias,
                                chapter=chapter,
                                url=urljoin('https://mangadex.org', url),
                                groups=groups, title=title)
            chapters = [c] + chapters
        return chapters

    @property
    def name(self):
        title_re = re.compile(r'^(.+) \(Manga\) - MangaDex')
        title = self.soup.find('title').string.strip()
        return re.search(title_re, title).group(1)


class MangadexChapter(BaseChapter):
    # match /chapter/12345 and avoid urls like /chapter/1235/comments
    url_re = re.compile(
        r'(?:https?://mangadex\.(?:org|com))?/chapter/([0-9]+)'
        r'(?:/[^a-zA-Z0-9]|/?$)'
    )
    # There is an inlined js with a bunch of useful variables
    hash_re = re.compile(r'var dataurl ?= ?\'([A-Za-z0-9]{32})\'')
    # Example: (mind that the trailing comma is invalid json)
    # var page_array = [
    # 'x1.jpg','x2.jpg','x3.jpg','x4.jpg','x5.jpg','x6.png',];
    pages_re = re.compile(r'var page_array ?= ?\[([^\]]+)\]', re.DOTALL)
    # Just extract the single page name like: x1.jpg
    single_page_re = re.compile(r'\s?\'([^\']+)\',?')
    # This can be a mirror server or data path. Example:
    # var server = 'https://s2.mangadex.org/'
    # var server = '/data/'
    server_re = re.compile(r'var server ?= ?\'([^\']+)\'')
    uses_pages = True

    @staticmethod
    def _reader_get(url, page_index):
        return requests.get(url)

    def available(self):
        self.r = self.reader_get(1)
        if not len(self.r.text):
            return False
        elif self.r.status_code == 404:
            return False
        elif re.search(re.compile(r'Chapter #[0-9]+ does not exist.'),
                       self.r.text):
            return False
        else:
            return True

    def download(self):
        if getattr(self, 'r', None):
            r = self.r
        else:
            r = self.reader_get(1)
        soup = BeautifulSoup(r.text, config.get().html_parser)
        chapter_hash = re.search(self.hash_re, r.text).group(1)
        pages_var = re.search(self.pages_re, r.text)
        pages = re.findall(self.single_page_re, pages_var.group(1))
        files = [None] * len(pages)
        mirror = re.search(self.server_re, r.text).group(1)
        server = urljoin('https://mangadex.org', mirror)
        futures = []
        last_image = None
        with self.progress_bar(pages) as bar:
            for i, page in enumerate(pages):
                if guess_type(page)[0]:
                    image = server + chapter_hash + '/' + page
                else:
                    print('Unkown image type for url {}'.format(page))
                    raise ValueError
                r = requests.get(image, stream=True)
                if r.status_code == 404:
                    r.close()
                    raise ValueError
                fut = download_pool.submit(self.page_download_task, i, r)
                fut.add_done_callback(partial(self.page_download_finish,
                                              bar, files))
                futures.append(fut)
                last_image = image
            concurrent.futures.wait(futures)
            self.create_zip(files)

    def from_url(url):
        r = MangadexChapter._reader_get(url, 1)
        soup = BeautifulSoup(r.text, config.get().html_parser)
        try:
            series_url = soup.find('a', href=MangadexSeries.url_re)['href']
        except TypeError:
            raise exceptions.ScrapingError('Chapter has no parent series link')
        series = MangadexSeries(urljoin('https://mangadex.org', series_url))
        for chapter in series.chapters:
            parsed_chapter_url = ''.join(urlparse(chapter.url)[1:])
            parsed_url = ''.join(urlparse(url)[1:])
            if parsed_chapter_url == parsed_url:
                return chapter

    def reader_get(self, page_index):
        return self._reader_get(self.url, page_index)
