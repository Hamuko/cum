from bs4 import BeautifulSoup
from mimetypes import guess_extension
from scrapers.base import BaseChapter, BaseSeries
from tempfile import NamedTemporaryFile
import os
import re
import requests

name_re = r'Ch\.([A-Za-z0-9\.\-]*)(?:\: (.*))?'


class BatotoSeries(BaseSeries):
    def __init__(self, url):
        r = requests.get(url)
        self.url = url
        self.soup = BeautifulSoup(r.text)
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
            name_parts = re.search(name_re, name)
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
    uses_pages = True

    def __init__(self, name=None, alias=None, chapter=None,
                 url=None, groups=[], title=None):
        self.name = name
        self.alias = alias
        self.chapter = chapter
        self.title = title
        self.url = url
        self.groups = groups

    def download(self):
        r = requests.get(self.url)
        soup = BeautifulSoup(r.text)
        pages = [x.get('value') for x in soup.find('select', id='page_select')
                                             .find_all('option')]
        files = []
        with self.progress_bar(pages) as bar:
            for page in bar:
                r = requests.get(page)
                soup = BeautifulSoup(r.text)
                image = soup.find('img', id='comic_page').get('src')
                r = requests.get(image, stream=True)
                ext = guess_extension(r.headers.get('content-type'))
                f = NamedTemporaryFile(suffix=ext)
                for chunk in r.iter_content(chunk_size=1024):
                    if chunk:
                        f.write(chunk)
                        f.flush()
                files.append(f)

        self.create_zip(files)
        self.mark_downloaded()
