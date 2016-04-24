from bs4 import BeautifulSoup
from cum import config, exceptions, output
from cum.scrapers.base import BaseChapter, BaseSeries, download_pool
from functools import partial
from mimetypes import guess_type
import concurrent.futures
import re
import requests


class BatotoSeries(BaseSeries):
    url_re = re.compile(r'https?://bato\.to/comic/_/comics/')
    name_re = re.compile(r'Ch\.([A-Za-z0-9\.\-]*)(?:\: (.*))?')

    def __init__(self, url, **kwargs):
        super().__init__(url, **kwargs)
        r = requests.get(url, cookies=config.get().batoto.login_cookies)
        self.soup = BeautifulSoup(r.text, config.get().html_parser)
        self.chapters = self.get_chapters()

    def get_chapters(self):
        if self.soup.find('div', id='register_notice'):
            raise exceptions.LoginError('Batoto login error')
        rows = self.soup.find_all('tr', class_="row lang_English chapter_row")
        chapters = []
        for row in rows:
            columns = row.find_all('td')

            name = columns[0].img.next_sibling.strip()
            name_parts = re.search(self.name_re, name)
            chapter = name_parts.group(1)
            title = name_parts.group(2)

            url = columns[0].find('a').get('href')

            groups = [g.string for g in columns[2].find_all('a')]

            c = BatotoChapter(name=self.name, alias=self.alias,
                              chapter=chapter, url=url,
                              groups=groups, title=title)
            chapters.append(c)
        return chapters

    @property
    def name(self):
        return self.soup.find('h1').string.strip()


class BatotoChapter(BaseChapter):
    error_re = re.compile(r'ERROR \[10010\]')
    img_path_re = re.compile(
        r'(http://img.bato.to/comics/.*?/img)([0-9]*)(\.[A-Za-z]+)'
    )
    ch_img_path_re = re.compile(
        r'(http://img.bato.to/comics/.*?/ch[0-9]*p)([0-9]*)(\.[A-Za-z]+)'
    )
    next_img_path_re = re.compile(r'img.src = "(.+)";')
    url_re = re.compile(r'https?://bato.to/reader#(.*)')
    uses_pages = True

    @staticmethod
    def _reader_get(chapter_hash, page_index):
        return requests.get('http://bato.to/areader',
                            params={'id': chapter_hash, 'p': page_index},
                            headers={'Referer': 'http://bato.to/reader'},
                            cookies=config.get().batoto.login_cookies)

    def available(self):
        if not self.batoto_hash:
            return False
        self.r = self.reader_get(1)
        if not len(self.r.text):
            return False
        elif self.r.status_code == 404:
            return False
        elif "The thing you're looking for is unavailable." in self.r.text:
            if "Try logging in" not in self.r.text:
                return False
            else:
                return True
        else:
            return True

    @property
    def batoto_hash(self):
        hash_match = re.search(self.url_re, self.url)
        if hash_match:
            return hash_match.group(1)
        else:
            return None

    def download(self):
        if getattr(self, 'r', None):
            r = self.r
        else:
            r = self.reader_get(1)
        soup = BeautifulSoup(r.text, config.get().html_parser)
        if soup.find('a', href='#{}_1_t'.format(self.batoto_hash)):
            # The chapter uses webtoon layout, meaning all of the images are on
            # the same page.
            pages = [''.join(i) for i in re.findall(self.img_path_re, r.text)]
        else:
            pages = [x.get('value') for x in
                     soup.find('select', id='page_select').find_all('option')]
            if not pages:
                output.warning('Skipping {s.name} {s.chapter}: '
                               'chapter has no pages'
                               .format(s=self))
                return
            # Replace the first URL with the first image URL to avoid scraping
            # the first page twice.
            pages[0] = soup.find('img', id='comic_page').get('src')
            next_match = re.search(self.next_img_path_re, r.text)
            if next_match:
                pages[1] = next_match.group(1)
        files = [None] * len(pages)
        futures = []
        last_image = None
        with self.progress_bar(pages) as bar:
            for i, page in enumerate(pages):
                try:
                    if guess_type(page)[0]:
                        image = page
                    else:   # Predict the next URL based on the last URL
                        for reg in [self.img_path_re, self.ch_img_path_re]:
                            m = re.match(reg, last_image)
                            if m:
                                break
                        else:
                            raise ValueError
                        mg = list(m.groups())
                        num_digits = len(mg[1])
                        mg[1] = "{0:0>{digits}}".format(int(mg[1]) + 1,
                                                        digits=num_digits)
                        image = "".join(mg)
                    r = requests.get(image, stream=True)
                    if r.status_code == 404:
                        r.close()
                        raise ValueError
                except ValueError:  # If we fail to do prediction, scrape
                    r = self.reader_get(i + 1)
                    soup = BeautifulSoup(r.text, config.get().html_parser)
                    image = soup.find('img', id='comic_page').get('src')
                    image2_match = re.search(self.next_img_path_re, r.text)
                    if image2_match:
                        pages[i + 1] = image2_match.group(1)
                    r = requests.get(image, stream=True)
                fut = download_pool.submit(self.page_download_task, i, r)
                fut.add_done_callback(partial(self.page_download_finish,
                                              bar, files))
                futures.append(fut)
                last_image = image
            concurrent.futures.wait(futures)
            self.create_zip(files)

    def from_url(url):
        chapter_hash = re.search(BatotoChapter.url_re, url).group(1)
        r = BatotoChapter._reader_get(chapter_hash, 1)
        soup = BeautifulSoup(r.text, config.get().html_parser)
        try:
            series_url = soup.find('a', href=BatotoSeries.url_re)['href']
        except TypeError:
            raise exceptions.ScrapingError('Chapter has no parent series link')
        series = BatotoSeries(series_url)
        for chapter in series.chapters:
            if chapter.url == url:
                return chapter

    def reader_get(self, page_index):
        return self._reader_get(self.batoto_hash, page_index)
