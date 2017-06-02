from cum.scrapers.base import BaseChapter, BaseSeries, download_pool
from functools import partial
from urllib.parse import urljoin
import concurrent.futures
import re
import requests

name_re = re.compile(r'(?P<type>Chapter|Special) (?P<num>[0-9\.]+)(?:$|\: )'
                     r'(?P<title>.*)')
fallback_re = re.compile(r'(?P<num>.*?)(?:$|\: )(?P<title>.*)')


class DynastyScansSeries(BaseSeries):
    url_re = re.compile(r'https?://dynasty-scans\.com/series/')

    def __init__(self, url, **kwargs):
        super().__init__(url, **kwargs)
        url = url.replace('http://', 'https://')
        if url.endswith('/'):
            url = url[:-1]
        jurl = url + '.json'
        self.json = requests.get(jurl).json()
        self.chapters = self.get_chapters()

    def get_chapters(self):
        chapters = []
        for t in self.json['taggings']:
            if 'permalink' in t and 'title' in t:
                name_parts = re.search(name_re, t['title'])
                if not name_parts:
                    name_parts = re.search(fallback_re, t['title'])
                    chapter = name_parts.group('num')
                elif name_parts.group('type') == 'Special':
                    chapter = 'Special ' + name_parts.group('num')
                else:
                    chapter = name_parts.group('num')
                title = name_parts.group('title')
                url = urljoin('https://dynasty-scans.com/chapters/',
                              t['permalink'])
                c = DynastyScansChapter(name=self.name, alias=self.alias,
                                        chapter=chapter, url=url, title=title)
                chapters.append(c)
        return chapters

    @property
    def name(self):
        return self.json['name']


class DynastyScansChapter(BaseChapter):
    url_re = re.compile(r'https?://dynasty-scans\.com/chapters/')
    uses_pages = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.groups:
            self.groups = self.get_groups()

    def download(self):
        data = requests.get(self.url + '.json').json()
        pages = [urljoin('https://dynasty-scans.com',
                 u['url']) for u in data['pages']]
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
        url = url.replace('http://', 'https://')
        if url.endswith('/'):
            url = url[:-1]
        j = requests.get(url + '.json').json()
        author_link = None
        for t in j['tags']:
            if t['type'] == 'Series':
                series_url = urljoin('https://dynasty-scans.com/series/',
                                     t['permalink'])
                series = DynastyScansSeries(series_url)
                for chapter in series.chapters:
                    if chapter.url == url:
                        return chapter
            elif t['type'] == 'Author':
                author_link = urljoin('https://dynasty-scans.com/authors/',
                                      t['permalink'])
        if author_link:
            series = DynastyScansSeries(author_link)
            for chapter in series.chapters:
                if chapter.url == url:
                    return chapter
        # if the chapter is a one-shot
        name = j['title']
        return DynastyScansChapter(name=name, chapter='0', url=url)

    def get_groups(self):
        data = requests.get(self.url + '.json').json()
        groups = []
        for t in data['tags']:
            if t['type'] == 'Scanlator':
                groups.append(t['name'])
        return groups
