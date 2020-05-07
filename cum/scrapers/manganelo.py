from bs4 import BeautifulSoup
from cum import config, exceptions, output
from cum.scrapers.base import BaseChapter, BaseSeries, download_pool
from functools import partial
from warnings import filterwarnings
import concurrent.futures
import json
import re
import requests


class ManganeloSeries(BaseSeries):
    url_re = re.compile(r'https?://manganelo\.com/manga/.+')

    def __init__(self, url, **kwargs):
        super().__init__(url, **kwargs)
        filterwarnings(action = "ignore", message = "unclosed", category = ResourceWarning)
        spage = requests.get(url)
        if spage.status_code == 404:
            raise exceptions.ScrapingError
        self.soup = BeautifulSoup(spage.text, config.get().html_parser)
        # 404 pages actually return HTTP 200
        if self.soup.find("title").text == "404 Not Found":
            raise exceptions.ScrapingError
        self.chapters = self.get_chapters()

    def get_chapters(self):
        try:
            rows = self.soup.find_all("li", class_="a-h")
        except AttributeError:
            raise exceptions.ScrapingError()
        chapters = []
        for i, row in enumerate(rows):
            chap_num = re.match(r"https?://manganelo\.com/chapter/.+/?chapter_([0-9\.]+)",
                                row.find("a")["href"]).groups()[0]
            chap_url = row.find("a")["href"]
            chap_name = row.find("a")["title"]
            chap_date = row.find_all("span")[1]["title"]
            result = ManganeloChapter(name=self.name,
                                     alias=self.alias,
                                     chapter=chap_num,
                                     url=chap_url,
                                     title=chap_name,
                                     groups=[],
                                     upload_date=chap_date)
            chapters.append(result)
        return chapters

    @property
    def name(self):
        try:
            return re.match(r"(.+) Manga Online Free - Manganelo",
                            self.soup.find("title").text).groups()[0]
        except AttributeError:
            raise exceptions.ScrapingError


class ManganeloChapter(BaseChapter):
    url_re = re.compile((r'https?://manganelo\.com/'
                        r'chapter/.+/chapter_[0-9\.]'))
    upload_date = None
    uses_pages = True

    # 404 pages actually return HTTP 200
    # thus this method override
    def available(self):
        if not getattr(self, "cpage", None):
            self.cpage = requests.get(self.url)
        if not getattr(self, "soup", None):
            self.soup = BeautifulSoup(self.cpage.text,
                                      config.get().html_parser)
        return self.soup.find("title").text != "404 Not Found"

    def download(self):
        if not getattr(self, "cpage", None):
            self.cpage = requests.get(self.url)
        if not getattr(self, "soup", None):
            self.soup = BeautifulSoup(self.cpage.text,
                                      config.get().html_parser)

        # 404 pages actually return HTTP 200
        if self.soup.find("title").text == "404 Not Found":
            raise exceptions.ScrapingError
        pages = [ image["src"] for image in self.soup.find("div", class_ = "container-chapter-reader").find_all("img") ]

        futures = []
        files = [None] * len(pages)
        req_session = requests.Session()
        with self.progress_bar(pages) as bar:
            for i, page in enumerate(pages):
                retries = 0
                while retries < 10:
                    try:
                        r = req_session.get(page, stream=True)
                        if r.status_code != 200:
                            output.warning('Failed to fetch page with status {}, retrying #{}'
                                            .format(str(r.status_code), str(retries)))
                            retries += 1
                        else:
                            break
                    except requests.exceptions.ConnectionError:
                        retries += 1
                if r.status_code != 200:
                    output.error('Failed to fetch page with status {}, giving up'
                                    .format(str(r.status_code)))
                    raise ValueError
                fut = download_pool.submit(self.page_download_task, i, r)
                fut.add_done_callback(partial(self.page_download_finish,
                                              bar, files))
                futures.append(fut)
            concurrent.futures.wait(futures)
            self.create_zip(files)
            req_session.close()

    def from_url(url):
        cpage = requests.get(url)
        soup = BeautifulSoup(cpage.text, config.get().html_parser)
        iname = re.match("https?://manganelo\.com/chapter/(.+)/chapter_[0-9\.]+",
                            url).groups()[0]
        series = ManganeloSeries("https://manganelo.com/manga/" + iname)
        for chapter in series.chapters:
            if chapter.url == url:
                return chapter
        return None
