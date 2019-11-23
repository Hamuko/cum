from bs4 import BeautifulSoup
from cum import config, exceptions, output
from cum.scrapers.base import BaseChapter, BaseSeries, download_pool
from functools import partial
import concurrent.futures
import re
import requests


class MangahereSeries(BaseSeries):
    url_re = re.compile(r'https?://((www|m)\.)?mangahere\.cc/manga/.+')

    def __init__(self, url, **kwargs):
        super().__init__(url, **kwargs)
        # convert desktop link to mobile
        # bypasses adult content warning js
        spage = requests.get(url.replace("www.", "m."))
        if spage.status_code == 404:
            raise exceptions.ScrapingError
        self.soup = BeautifulSoup(spage.text, config.get().html_parser)
        self.chapters = self.get_chapters()

    def get_chapters(self):
        try:
            rows = self.soup.find("div", class_="manga-chapters")\
                .find("ul").find_all("li")
        except AttributeError:
            raise exceptions.ScrapingError()
        chapters = []
        for i, row in enumerate(rows):
            chap_num = re.match((r"//m\.mangahere\.cc"
                                r"/manga/[^/]+((/v[0-9]+)?"
                                r"/c[0-9\.]+)/?$"),
                                row.find("a")["href"]).groups()[0]\
                                .replace("/", "")
            if "v" in chap_num:
                chap_num = chap_num.replace("v", "").replace("c", ".")
            else:
                chap_num = chap_num.replace("c", "")
            if chap_num == "000":
                chap_num = "0"
            else:
                chap_num = chap_num.lstrip("0")
            # convert mobile link to desktop
            chap_url = "https:" + row.find("a")["href"]\
                .replace("/roll_manga/", "/manga/")\
                .replace("m.", "www.")
            chap_name = row.text
            result = MangahereChapter(name=self.name,
                                      alias=self.alias,
                                      chapter=chap_num,
                                      url=chap_url,
                                      title=chap_name,
                                      groups=[])
            chapters.append(result)
        return chapters

    @property
    def name(self):
        try:
            return re.match(r"(.+) - MangaHere Mobile$",
                            self.soup.find("title").text).groups()[0]
        except AttributeError:
            raise exceptions.ScrapingError


class MangahereChapter(BaseChapter):
    url_re = re.compile((r'https?://((www|m)\.)?mangahere\.cc'
                        r'/(roll_)?manga/[^/]+(/v[0-9]+)?/c[0-9\.]+/[0-9]+\.html$'))
    upload_date = None
    uses_pages = True

    def download(self):
        if not getattr(self, "cpage", None):
            self.cpage = requests.get(self.url.replace("www.", "m.")
                                      .replace("/manga/", "/roll_manga/"))
            if self.cpage.status_code == 404:
                raise exceptions.ScrapingError
        if not getattr(self, "soup", None):
            self.soup = BeautifulSoup(self.cpage.text,
                                      config.get().html_parser)

        image_list = self.soup.find("div", class_="mangaread-img")\
            .find_all("img")
        pages = []
        for image in image_list:
            pages.append(image["data-original"].replace("http://", "https://"))

        futures = []
        files = [None] * len(pages)
        req_session = requests.Session()
        with self.progress_bar(pages) as bar:
            for i, page in enumerate(pages):
                retries = 0
                while retries < 10:
                    try:
                        r = req_session.get(page, stream=True)
                        break
                    except requests.exceptions.ConnectionError:
                        retries += 1
                if r.status_code != 200:
                    r.close()
                    output.error("Page download got status code {}".format(str(r.status_code)))
                    raise ValueError
                fut = download_pool.submit(self.page_download_task, i, r)
                fut.add_done_callback(partial(self.page_download_finish,
                                              bar, files))
                futures.append(fut)
            concurrent.futures.wait(futures)
            self.create_zip(files)

    def from_url(url):
        chap_num = re.match((r"https?://((www|m)\.)?mangahere\.cc/(roll_)?"
                             r"manga/[^/]+((/v[0-9]+)?/c[0-9\.]+)"
                             r"/[0-9]+\.html"), url)\
            .groups()[3].replace("/", "")
        if "v" in chap_num:
            chap_num = chap_num.replace("v", "").replace("c", ".")
        else:
            chap_num = chap_num.replace("c", "")
        if chap_num == "000":
            chap_num = "0"
        else:
            chap_num = chap_num.lstrip("0")
        parent_url = re.match((r"(https?://((www|m)\.)?mangahere\.cc/(roll_)?"
                               r"manga/[^/]+)(/v[0-9]+)?/"
                               r"c[0-9\.]+/[0-9]+\.html"),
                              url).groups()[0]
        series = MangahereSeries(parent_url)
        for chapter in series.chapters:
            if chapter.chapter == str(chap_num):
                return chapter
        return None
