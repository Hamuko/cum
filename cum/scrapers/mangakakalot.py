from bs4 import BeautifulSoup
from cum import config, exceptions
from cum.scrapers.base import BaseChapter, BaseSeries, download_pool
from functools import partial
import concurrent.futures
import re
import requests


class MangaKakalotSeries(BaseSeries):
    chapter_re = re.compile(r'https://mangakakalot\.com/chapter/'
                            r'(?P<series>\w+)/chapter_(?P<chapter>\d+(\.\d+)?)')
    url_re = re.compile(r'https://mangakakalot\.com/manga/')

    def __init__(self, url, **kwargs):
        super().__init__(url, **kwargs)

        response = requests.get(url)
        self.soup = BeautifulSoup(response.content, config.get().html_parser)

        # mangakakalot does not return 404 if there is no such title
        try:
            self.cached_name = self.soup.select('.manga-info-text h1')[0].text
        except IndexError:
            raise exceptions.ScrapingError()

        self.chapters = self.get_chapters()

    def get_chapters(self):
        chapter_links = self.soup.select('.chapter-list a')
        chapters = []
        for chapter_link in chapter_links:
            url = chapter_link.attrs['href']
            chapter_info = self.chapter_re.search(url)
            chapter = chapter_info.group('chapter')
            # TODO: chapter titles, how do they work?
            c = MangaKakalotChapter(name=self.cached_name, alias=self.alias,
                                    chapter=chapter,
                                    url=url, groups=[])
            chapters.append(c)
        return chapters

    @property
    def name(self):
        return self.cached_name


class MangaKakalotChapter(BaseChapter):
    uses_pages = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        url = kwargs.get('url')
        response = requests.get(url)
        soup = BeautifulSoup(response.content, config.get().html_parser)
        self.pages = soup.select('.vung-doc img')

    def available(self):
        if len(self.pages) < 1:
            return False
        else:
            return True

    def download(self):
        files = [None] * len(self.pages)
        futures = []
        with self.progress_bar(self.pages) as bar:
            for i, page in enumerate(self.pages):
                r = requests.get(page.attrs['src'], stream=True)
                fut = download_pool.submit(self.page_download_task, i, r)
                fut.add_done_callback(partial(self.page_download_finish,
                                              bar, files))
                futures.append(fut)
            concurrent.futures.wait(futures)
            self.create_zip(files)

    @staticmethod
    def from_url(url):
        pattern = MangaKakalotSeries.chapter_re
        series_name = pattern.search(url).group('series')
        series_url = 'https://mangakakalot.com/manga/{}'.format(series_name)
        series = MangaKakalotSeries(series_url)
        for chapter in series.chapters:
            if chapter.url == url:
                return chapter
        return []
