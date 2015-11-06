from bs4 import BeautifulSoup
from cum import output
from cum.config import config
from cum.scrapers.base import BaseChapter, BaseSeries
from mimetypes import guess_extension, guess_type
from tempfile import NamedTemporaryFile
import os
import re
import requests


class BatotoSeries(BaseSeries):
    url_re = re.compile(r'https?://bato\.to/comic/_/comics/')
    name_re = re.compile(r'Ch\.([A-Za-z0-9\.\-]*)(?:\: (.*))?')

    def __init__(self, url):
        r = requests.get(url, cookies=config.batoto.login_cookies)
        self.url = url
        self.soup = BeautifulSoup(r.text, config.html_parser)
        self.chapters = self.get_chapters()

    @property
    def name(self):
        return self.soup.find('h1').string.strip()

    def get_chapters(self):
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


class BatotoChapter(BaseChapter):
    error_re = re.compile(r'ERROR \[10010\]')
    img_path_re = re.compile(
        r'(http://img.bato.to/comics/.*?/img)([0-9]*)(\.[A-Za-z]+)'
    )
    next_img_path_re = re.compile(r'img.src = "(.+)";')
    url_re = re.compile(r'https?://bato.to/reader#(.*)')
    uses_pages = True

    def __init__(self, name=None, alias=None, chapter=None,
                 url=None, groups=[], title=None):
        self.name = name
        self.alias = alias
        self.chapter = chapter
        self.title = title
        self.url = url
        self.groups = groups

    def available(self):
        hash_match = re.search(self.url_re, self.url)
        if hash_match:
            self.hash = hash_match.group(1)
        else:
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

    def from_url(url):
        r = requests.get(url, cookies=config.batoto.login_cookies)
        soup = BeautifulSoup(r.text, config.html_parser)
        series_url = soup.find('a', href=BatotoSeries.url_re)['href']
        series = BatotoSeries(series_url)
        for chapter in series.chapters:
            if chapter.url == url:
                return chapter

    def download(self):
        if getattr(self, 'r', None):
            r = self.r
        else:
            r = self.reader_get(1)
        soup = BeautifulSoup(r.text, config.html_parser)
        if soup.find('a', href=self.url + '_1_t'):
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
        files = []
        with self.progress_bar(pages) as bar:
            for page in bar:
                if guess_type(page)[0]:
                    image = page
                else:
                    r = self.reader_get(pages.index(page) + 1)
                    soup = BeautifulSoup(r.text, config.html_parser)
                    image = soup.find('img', id='comic_page').get('src')
                    image2_match = re.search(self.next_img_path_re, r.text)
                    if image2_match:
                        pages[pages.index(page) + 1] = image2_match.group(1)
                r = requests.get(image, stream=True)
                ext = guess_extension(r.headers.get('content-type'))
                f = NamedTemporaryFile(suffix=ext)
                for chunk in r.iter_content(chunk_size=4096):
                    if chunk:
                        f.write(chunk)
                f.flush()
                files.append(f)

        self.create_zip(files)

    def reader_get(self, page_index):
        return requests.get('http://bato.to/areader',
                            params={'id': self.hash, 'p': page_index},
                            headers={'Referer': 'http://bato.to/reader'},
                            cookies=config.batoto.login_cookies)
