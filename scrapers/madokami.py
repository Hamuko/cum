from bs4 import BeautifulSoup
from config import config
from scrapers.base import BaseChapter, BaseSeries
from urllib.parse import urljoin
import db
import output
import re
import requests

name_re = r'-? c([0-9-]+).*?(?: \[(.*)\])?\.'
fallback_re = r'\- (.*) (?:\[(.*)\])?'


class MadokamiSeries(BaseSeries):
    def __init__(self, url):
        r = requests.get(url)
        self.url = url
        self.soup = BeautifulSoup(r.text, config.html_parser)
        self.chapters = self.get_chapters()

    @property
    def name(self):
        return self.soup.find('span', class_='title').string

    def get_chapters(self):
        rows = (self.soup
                .find('table', class_='mobile-files-table')
                .find_all('tr'))
        chapters = []
        for row in rows[1:]:
            # If the Read link cannot be found in the current row, the row is
            # assumed to be a non-manga file uploaded to the directory and will
            # thus be skipped.
            if not row.find('a', text='Read'):
                continue

            link = row.find('a')

            url = urljoin(self.url, link.get('href'))

            name = link.string
            name_parts = re.search(name_re, name)
            if not name_parts:
                name_parts = re.search(fallback_re, name)
            chapter = name_parts.group(1)
            if name_parts.group(2):
                groups = name_parts.group(2).split('][')
            else:
                groups = []

            c = MadokamiChapter(name=self.name, alias=self.alias,
                                chapter=chapter, url=url, groups=groups)
            chapters.append(c)
        return chapters


class MadokamiChapter(BaseChapter):
    uses_pages = False

    def __init__(self, name=None, alias=None, chapter=None,
                 url=None, groups=[], title=None):
        self.name = name
        self.alias = alias
        self.chapter = chapter
        self.title = title
        self.url = url
        self.groups = groups

    def download(self):
        auth = requests.auth.HTTPBasicAuth(*config.madokami.login)
        r = requests.get(self.url, auth=auth, stream=True)
        total_length = r.headers.get('content-length')
        if not r.headers.get('content-disposition'):
            output.error('Invalid login')
            exit(1)

        with open(self.filename, 'wb') as f:
            if total_length is None:
                f.write(r.content)
            else:
                total_length = int(total_length)
                with self.progress_bar(total_length) as bar:
                    for chunk in r.iter_content(chunk_size=1024):
                        if chunk:
                            bar.update(len(chunk))
                            f.write(chunk)
                            f.flush()

        self.mark_downloaded()
