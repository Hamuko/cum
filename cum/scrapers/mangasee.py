from bs4 import BeautifulSoup
from cum import config, exceptions, output
from cum.scrapers.base import BaseChapter, BaseSeries, download_pool
from functools import partial
import concurrent.futures
import json
import re
import requests


class MangaseeSeries(BaseSeries):
    url_re = re.compile(r'https?://mangaseeonline\.us/manga/.+')
    multi_season_regex = re.compile((r"(https?://mangaseeonline\.us)"
                                     r"?/read-online/"
                                     r".+-chapter-[0-9\.]+-index-"
                                     r"([0-9]+)-page-[0-9]+\.html"))

    def __init__(self, url, **kwargs):
        super().__init__(url, **kwargs)
        spage = requests.get(url)
        if spage.status_code == 404:
            raise exceptions.ScrapingError
        self.soup = BeautifulSoup(spage.text, config.get().html_parser)
        self.chapters = self.get_chapters()

    def _get_chapnum_multiseason_series(self, url, chap_num):
        if not re.match(self.multi_season_regex, url):
            # chapter is from season 1
            return "01." + chap_num.zfill(3)
        else:
            # chapter is from season >1
            season = re.match(self.multi_season_regex, url).groups()[1]
            return season.zfill(2) + "." + chap_num.zfill(3)

    def get_chapters(self):
        try:
            rows = self.soup.find_all("a", class_="list-group-item")
        except AttributeError:
            raise exceptions.ScrapingError()
        chapters = []
        for i, row in enumerate(rows):
            chap_num = re.match(r"Read .+ Chapter ([0-9\.]+) For Free Online",
                                row["title"]).groups()[0]
            if not hasattr(self, "is_multi_season"):
                if re.match(self.multi_season_regex, row["href"]):
                    self.is_multi_season = True
            chap_url = "https://mangaseeonline.us" + row["href"]
            chap_name = row.find("span").text
            chap_date = row.find("time").text
            result = MangaseeChapter(name=self.name,
                                     alias=self.alias,
                                     chapter=chap_num,
                                     url=chap_url,
                                     title=chap_name,
                                     groups=[],
                                     upload_date=chap_date)
            chapters.append(result)
        # the chapters in the first season of a multi-season title
        # are indistinguishable from a non-multi-season title.  thus
        # we must retroactively reanalyze all chapters and adjust
        # chapter numbers if *any* are multi-season
        if hasattr(self, "is_multi_season"):
            for chapter in chapters:
                chapter.chapter = self.\
                    _get_chapnum_multiseason_series(chapter.url,
                                                    chapter.chapter)

        return chapters

    @property
    def name(self):
        try:
            return re.match(r"Read (.+) Man[a-z]+ For Free  \| MangaSee",
                            self.soup.find("title").text).groups()[0]
        except AttributeError:
            raise exceptions.ScrapingError


class MangaseeChapter(BaseChapter):
    url_re = re.compile((r'https?://mangaseeonline\.us/'
                        r'read-online/.+-chapter-[0-9\.]+-page-[0-9]+\.html'))
    upload_date = None
    uses_pages = True

    def download(self):
        if not getattr(self, "cpage", None):
            self.cpage = requests.get(self.url)
        if not getattr(self, "soup", None):
            self.soup = BeautifulSoup(self.cpage.text,
                                      config.get().html_parser)

        for script in self.soup.find_all("script"):
            if len(script.contents) and re.match("\n\tChapterArr=.+", script.contents[0]):
                image_list = script.contents[0]
                continue

        image_list = re.sub("\n\tChapterArr=", "", image_list)
        image_list = re.sub(";\n\t?", "", image_list)
        image_list = re.sub("PageArr=", ",", image_list)
        image_list = "[" + image_list + "]"
        image_list = json.loads(image_list)[1]
        pages = []
        for image in image_list:
            if image != "CurPage":
                if re.match(".+blogspot.+", image_list[image]):
                    image_list[image] = image_list[image].\
                                        replace("http://", "https://")
                pages.append(image_list[image])

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
                    raise exceptions.ScrapingError
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
        # chap_num = soup.find("span", class_="CurChapter").text
        iname = soup.find("a", class_="list-link")["href"]
        series = MangaseeSeries("https://mangaseeonline.us" + iname)
        for chapter in series.chapters:
            if chapter.url == url:
                return chapter
        return None
