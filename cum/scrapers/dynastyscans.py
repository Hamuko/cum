from bs4 import BeautifulSoup
from cum import config
from cum.scrapers.base import BaseChapter, BaseSeries, download_pool
from functools import partial
from urllib.parse import urljoin
import concurrent.futures
import re
import requests

name_re = re.compile(r'Chapter ([0-9\.]+)(?:$|\: )(.*)')
fallback_re = re.compile(r'(.*?)(?:$|\: )(.*)')


class DynastyScansSeries(BaseSeries):
    url_re = re.compile(r'http://dynasty-scans\.com/series/')

    def __init__(self, url, **kwargs):
        super().__init__(url, **kwargs)
        r = requests.get(url)
        self.soup = BeautifulSoup(r.text, config.get().html_parser)
        self.chapters = self.get_chapters()

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

    @property
    def name(self):
        return self.soup.find('h2', class_='tag-title').contents[0].string


class DynastyScansChapter(BaseChapter):
    url_re = re.compile(r'http://dynasty-scans\.com/chapters/')
    uses_pages = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.groups:
            self.groups = self.get_groups()

    def download(self):
        r = requests.get(self.url)
        pages = re.findall(r'"image":"(.*?)"', r.text)
        files = [None] * len(pages)
        futures = []
        with self.progress_bar(pages) as bar:
            for i, page in enumerate(pages):
                r = requests.get(urljoin(self.url, page), stream=True)
                fut = download_pool.submit(self.page_download_task, i, r)
                fut.add_done_callback(partial(self.page_download_finish,
                                              bar, files))
                futures.append(fut)
            concurrent.futures.wait(futures)
            self.create_zip(files)

    def from_url(url):
        r = requests.get(url)
        soup = BeautifulSoup(r.text, config.get().html_parser)
        series_url = urljoin(url,
                             soup.find('h3', id='chapter-title').a['href'])
        try:
            series = DynastyScansSeries(series_url)
        except:
            name = soup.find('h3', id='chapter-title').b.text
            return DynastyScansChapter(name=name, chapter='0', url=url)
        else:
            for chapter in series.chapters:
                if chapter.url == url:
                    return chapter
        return None

    def get_groups(self):
        r = requests.get(self.url)
        soup = BeautifulSoup(r.text, config.get().html_parser)
        scanlators = soup.find('span', class_='scanlators')
        if scanlators:
            links = scanlators.find_all('a')
        else:
            links = []
        groups = []
        for link in links:
            r = requests.get(urljoin(self.url, link.get('href')))
            s = BeautifulSoup(r.text, config.get().html_parser)
            g = s.find('h2', class_='tag-title').b.string
            groups.append(g)
        return groups
