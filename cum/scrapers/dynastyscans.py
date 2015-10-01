from bs4 import BeautifulSoup
from cum.config import config
from cum.scrapers.base import BaseChapter, BaseSeries
from mimetypes import guess_extension
from tempfile import NamedTemporaryFile
from urllib.parse import urljoin
import re
import requests

name_re = r'^[A-Za-z]* ([0-9\-]+)(?:\: (.*))?'
fallback_re = r'^([A-Za-z0-9 ]*)(?:\: (.*))?'


class DynastyScansSeries(BaseSeries):
    url_re = re.compile(r'http://dynasty-scans\.com/series/')

    def __init__(self, url):
        r = requests.get(url)
        self.url = url
        self.soup = BeautifulSoup(r.text, config.html_parser)
        self.chapters = self.get_chapters()

    @property
    def name(self):
        return self.soup.find('h2', class_='tag-title').contents[0].string

    def get_chapters(self):
        chapter_list = self.soup.find('dl', class_='chapter-list')
        links = chapter_list.find_all('a', class_='name')
        chapters = []
        for link in links:
            name_parts = re.search(name_re, link.string)
            if not name_parts:
                name_parts = re.search(fallback_re, link.string)
            chapter = name_parts.group(1)
            title = name_parts.group(2)
            url = urljoin(self.url, link.get('href'))
            c = DynastyScansChapter(name=self.name, alias=self.alias,
                                    chapter=chapter, url=url, title=title)
            chapters.append(c)
        return chapters


class DynastyScansChapter(BaseChapter):
    url_re = re.compile(r'http://dynasty-scans\.com/chapters/')
    uses_pages = True

    def __init__(self, name=None, alias=None, chapter=None,
                 url=None, groups=[], title=None):
        self.name = name
        self.alias = alias
        self.chapter = chapter
        self.title = title
        self.url = url
        self.groups = groups
        if not groups:
            self.groups = self.get_groups()

    def download(self):
        r = requests.get(self.url)
        pages = re.findall(r'"image":"(.*?)"', r.text)
        files = []
        with self.progress_bar(pages) as bar:
            for page in bar:
                r = requests.get(urljoin(self.url, page), stream=True)
                ext = guess_extension(r.headers.get('content-type'))
                f = NamedTemporaryFile(suffix=ext)
                for chunk in r.iter_content(chunk_size=1024):
                    if chunk:
                        f.write(chunk)
                        f.flush()
                files.append(f)

        self.create_zip(files)

    def from_url(url):
        r = requests.get(url)
        soup = BeautifulSoup(r.text, config.html_parser)
        series_url = urljoin(url,
                             soup.find('h3', id='chapter-title').a['href'])
        series = DynastyScansSeries(series_url)
        for chapter in series.chapters:
            if chapter.url == url:
                return chapter
        return None

    def get_groups(self):
        r = requests.get(self.url)
        soup = BeautifulSoup(r.text, config.html_parser)
        scanlators = soup.find('span', class_='scanlators')
        if scanlators:
            links = scanlators.find_all('a')
        else:
            links = []
        groups = []
        for link in links:
            r = requests.get(urljoin(self.url, link.get('href')))
            s = BeautifulSoup(r.text, config.html_parser)
            g = s.find('h2', class_='tag-title').b.string
            groups.append(g)
        return groups
