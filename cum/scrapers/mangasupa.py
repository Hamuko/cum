from bs4 import BeautifulSoup
from cum import config, exceptions
from cum.scrapers.base import BaseChapter, BaseSeries, download_pool
from functools import partial
from mimetypes import guess_type
from urllib.parse import urljoin, urlparse
import concurrent.futures
import re
import requests


class MangaSupaSeries(BaseSeries):
    url_re = re.compile(r'http://mangasupa\.com/manga/([^.]+)$')
    title_re = re.compile(r'Read (.*) Manga Online | Mangasupa')
    from_url_re = re.compile(r'http://mangasupa.com/chapter/([^/]+)')

    def __init__(self, url, **kwargs):
        super().__init__(url, **kwargs)
        r = requests.get(self.url)
        if r.status_code != 200:
            raise exceptions.ScrapingError()
        self.soup = BeautifulSoup(r.text, config.get().html_parser)
        self.chapters = self.get_chapters()

    @property
    def name(self):
        title = self.soup.find('title').string.strip()
        return re.search(self.title_re, title).group(1)

    def get_chapters(self):
        links = self.soup.find_all('a')
        chapters = []

        id = re.search(MangaSupaSeries.url_re, self.url).group(1)
        manga_name = self.name
        for a in links:
            url = a.get('href')
            url_match = (re.search(MangaSupaChapter.url_re, url)
                         if url else None)
            if url_match and url_match.group(1) == id:
                chapter = url_match.group(2)
                title = re.search(MangaSupaChapter.title_re, a.text)\
                          .group(1).strip()
                c = MangaSupaChapter(name=manga_name, alias=self.alias,
                                     chapter=chapter,
                                     url=url,
                                     groups=[], title=title)
                chapters = [c] + chapters

        return chapters


class MangaSupaChapter(BaseChapter):
    url_re = re.compile(
        r'http://mangasupa.com/chapter/([^/]+)/chapter_([0-9]+)'
    )
    title_re = re.compile(r'(?:vol[\.0-9 ]+)?chapter[\.0-9v ]+:?(.*)$')
    alt_re = re.compile(r'page [0-9]+ - MangaSupa.com')
    uses_pages = False

    def from_url(url):
        series_id = re.search(MangaSupaSeries.from_url_re, url).group(1)
        series = MangaSupaSeries("http://mangasupa.com/manga/" + series_id)
        for chapter in series.chapters:
            if chapter.url == url:
                return chapter
        return None

    def download(self):
        if getattr(self, 'r', None):
            r = self.r
        else:
            r = requests.get(self.url)

        soup = BeautifulSoup(r.text, config.get().html_parser)
        vung_doc = soup.find("div", {"class": "vung_doc"})
        pages = vung_doc.find_all("img")
        files = [None] * len(pages)
        futures = []
        assert len(pages) > 0

        with self.progress_bar(len(pages)) as bar:
            for i, page in enumerate(pages):
                r = requests.get(page.get('src'), stream=True)
                if r.status_code == 404:
                    r.close()
                    raise ValueError
                fut = download_pool.submit(self.page_download_task, i, r)
                fut.add_done_callback(partial(self.page_download_finish,
                                              bar, files))
                futures.append(fut)

            concurrent.futures.wait(futures)
            self.create_zip(files)
