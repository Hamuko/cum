from bs4 import BeautifulSoup
from cum import config, exceptions, output
from cum.scrapers.base import BaseChapter, BaseSeries, download_pool
from functools import partial
from mimetypes import guess_type
from urllib.parse import urljoin, urlparse
from time import sleep
from random import randrange
import concurrent.futures
import re
import requests
import json
from cum.version import __version__


class MangadexSeries(BaseSeries):
    url_re = re.compile(
        r'(?:https?://mangadex\.(?:org|cc))?/(?:manga|title)/([0-9]+)'
    )
    # TODO remove when there are properly spaced api calls
    spam_failures = 0
    headers = {"User-Agent": "cum/{}".format(__version__)}

    def __init__(self, url, **kwargs):
        super().__init__(url, **kwargs)
        self._get_page(self.url)
        self.chapters = self.get_chapters()

    def _get_page(self, url):
        manga_id = re.search(self.url_re, url)
        r = requests.get('https://mangadex.cc/api/manga/' + manga_id.group(1),
                         headers=MangadexSeries.headers)

        # TODO FIXME replace with properly spaced api calls
        #            This is a bad workaround for
        #                '503 please stop spaming the site'
        #            erros when making requests to /api/ urls quickly.
        #            It may still break when 4 calls are done at the same time
        sleep(randrange(0, 900) / 1000.0)
        if r.status_code == 503 and self.spam_failures < 3:
            # sleep 10-17 seconds to wait out the spam protection
            # and make it less likely for all threads to hit at the same time
            sleep(randrange(10000, 17000) / 1000.0)
            self.spam_failures = self.spam_failures + 1
            return self._get_page(url)
        elif self.spam_failures >= 3:
            print("Error: Mangadex server probably contacted too often\n")
            print(r.text)
            raise exceptions.ScrapingError("Mangadex spam error")

        self.spam_failures = 0
        self.json = json.loads(r.text)

    def get_chapters(self):
        result_chapters = []
        manga_name = self.name
        chapters = self.json['chapter'] if self.json.get('chapter') else []
        for c in chapters:
            url = 'https://mangadex.org/chapter/' + c
            chapter = chapters[c]['chapter']
            title = chapters[c]['title'] if chapters[c]['title'] else None
            language = chapters[c]['lang_code']
            # TODO: Add an option to filter by language.
            if language != 'gb':
                continue
            groups = [chapters[c]['group_name']]

            result = MangadexChapter(name=manga_name, alias=self.alias,
                                     chapter=chapter,
                                     url=url,
                                     groups=groups, title=title)
            result_chapters = [result] + result_chapters
        return result_chapters

    @property
    def name(self):
        return self.json['manga']['title']


class MangadexChapter(BaseChapter):
    # match /chapter/12345 and avoid urls like /chapter/1235/comments
    url_re = re.compile(
        r'(?:https?://mangadex\.(?:org|cc))?/chapter/([0-9]+)'
        r'(?:/[^a-zA-Z0-9]|/?$)'
    )
    uses_pages = True

    @staticmethod
    def _reader_get(url, page_index):
        chapter_id = re.search(MangadexChapter.url_re, url)
        api_url = "https://mangadex.cc/api/chapter/" + chapter_id.group(1)
        return requests.get(api_url, headers=MangadexSeries.headers)

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

        chapter_hash = self.json['hash']
        pages = self.json['page_array']
        files = [None] * len(pages)
        # This can be a mirror server or data path. Example:
        # var server = 'https://s2.mangadex.org/'
        # var server = '/data/'
        mirror = self.json['server']
        server = urljoin('https://mangadex.cc', mirror)
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
                if r.status_code >= 400:
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
        data = json.loads(r.text)
        manga_id = data['manga_id']
        series = MangadexSeries('https://mangadex.cc/manga/' + str(manga_id))
        for chapter in series.chapters:
            parsed_chapter_url = ''.join(urlparse(chapter.url)[1:])
            parsed_url = ''.join(urlparse(url)[1:])
            if parsed_chapter_url == parsed_url:
                return chapter

    def reader_get(self, page_index):
        r = self._reader_get(self.url, page_index)
        self.json = json.loads(r.text)
        return r
