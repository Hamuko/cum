from abc import ABCMeta
from cum import config, exceptions
from cum.scrapers.base import BaseChapter, BaseSeries, download_pool
from functools import partial
from tempfile import NamedTemporaryFile
from urllib.parse import urljoin, urlparse
import concurrent.futures
import re
import requests


class FoOlSlideSeries(BaseSeries, metaclass=ABCMeta):
    def __init__(self, url, directory=None, stub=None, use_https=False):
        self.url = url
        self.directory = directory
        self.stub = stub
        self.use_https = use_https
        self._page = 1
        self.get_comic_details()
        self.chapters = self.get_chapters()

    def _process_comic_list(self, response):
        """Iterates the JSON data provided by the list API and returns either
        the dictionary or None.
        """
        path = urlparse(self.url).path
        for comic in response['comics']:
            comic_path = urlparse(comic['href']).path
            if comic['stub'] == self.stub or comic_path == path:
                return comic

    @property
    def api_hook_details(self):
        path = 'api/reader/comic/id/{}'.format(self.foolslide_id)
        return urljoin(self.BASE_URL, path)

    @property
    def api_hook_list(self):
        path = 'api/reader/comics/page/{}'.format(self._page)
        return urljoin(self.BASE_URL, path)

    def get_comic_details(self):
        """Parses through the various series listed on Foolslide until a match
        with the specified series URL is found.
        """
        while True:
            response = requests.get(self.api_hook_list).json()
            if response.get('error', None) == 'Comics could not be found':
                raise exceptions.ScrapingError()
            result = self._process_comic_list(response)
            if result:
                break
            self._page += 1
        self.foolslide_id = result['id']
        self.name = result['name']

    def get_chapters(self, chapter_object):
        """Queries the series details API and creates a chapter object for each
        chapter listed.
        """
        response = requests.get(self.api_hook_details).json()
        chapters = []
        for chapter in response['chapters']:
            if int(chapter['chapter']['subchapter']) > 0:
                chapter_number = '.'.join([chapter['chapter']['chapter'],
                                           chapter['chapter']['subchapter']])
            else:
                chapter_number = chapter['chapter']['chapter']
            kwargs = {
                'name': self.name,
                'alias': self.alias,
                'chapter': chapter_number,
                'api_id': chapter['chapter']['id'],
                'url': chapter['chapter']['href'],
                'title': chapter['chapter']['name'],
                'groups': [team['name'] for team in chapter['teams']]
            }
            chapter = chapter_object(**kwargs)
            chapters.append(chapter)
        return chapters

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        self._name = value


class FoOlSlideChapter(BaseChapter, metaclass=ABCMeta):
    uses_pages = True
    chapter_id_re = re.compile(r'"chapter_id":"([0-9]*)"')
    url_name_re = re.compile(r'/read/(.*?)/')
    no_pages_re = re.compile(r'(^.*)page.*$')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.api_id = kwargs.get('api_id')
        if self.url.split("://")[0] == "https":
            self.use_https = True
        else:
            self.use_https = False

    @property
    def api_hook_details(self):
        path = 'api/reader/chapter/id/{}'.format(self.api_id)
        return urljoin(self.BASE_URL, path)

    def download(self):
        response = requests.get(self.api_hook_details).json()
        pages = response['pages']
        files = [None] * len(pages)
        futures = []
        with self.progress_bar(pages) as bar:
            for i, page in enumerate(pages):
                r = requests.get(page['url'], stream=True)
                fut = download_pool.submit(self.page_download_task, i, r)
                fut.add_done_callback(partial(self.page_download_finish,
                                              bar, files))
                futures.append(fut)
            concurrent.futures.wait(futures)
            self.create_zip(files)

    def from_url(url, series_object):
        url = re.search(FoOlSlideChapter.no_pages_re, url).group(1)
        url_name = re.search(FoOlSlideChapter.url_name_re, url).group(1)
        series = series_object(None, stub=url_name,
                               use_https=(url.split("://")[0] == "https"))
        for chapter in series.chapters:
            if chapter.url.split("://")[1] == url.split("://")[1]:
                return chapter
