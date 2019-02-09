from bs4 import BeautifulSoup
from cum import config, exceptions
from cum.scrapers.base import BaseChapter, BaseSeries, download_pool
from functools import partial
import concurrent.futures
import json
import re
import requests
import traceback


class MangaseeSeries(BaseSeries):
    url_re = re.compile(r'https?://mangaseeonline\.us/manga/.+')

    def __init__(self, url, **kwargs):
        super().__init__(url, **kwargs)
        spage = requests.get(url)
        self.soup = BeautifulSoup(spage.text, config.get().html_parser)
        self.chapters = self.get_chapters()

    def get_chapters(self):
        try:
            rows = self.soup.find_all("a", class_="list-group-item")
        except AttributeError:
            raise exceptions.ScrapingError()
        chapters = []
        for i, row in enumerate(rows):
            chap_num = re.match(r"Read .+ Chapter ([0-9\.]+) For Free Online",
                                row["title"]).groups()[0]
            chap_url = "https://mangaseeonline.us" + row["href"]
            chap_name = row.find_all("span")[0].text
            chap_date = row.find_all("time")[0].text
            result = MangaseeChapter(name=self.name,
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
            return re.match(r"Read (.+) Man[a-z]+ For Free  \| MangaSee",
                            self.soup.find_all("title")[0].text).groups()[0]
        except AttributeError:
            print(traceback.format_exc())
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
            if re.match("\n\tChapterArr=.+", script.text):
                image_list = script.text
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
        with self.progress_bar(pages) as bar:
            for i, page in enumerate(pages):
                retries = 0
                while retries < 10:
                    try:
                        r = requests.get(page, stream=True)
                        break
                    except requests.exceptions.ConnectionError:
                        retries += 1
                if r.status_code != 200:
                    r.close()
                    raise ValueError
                fut = download_pool.submit(self.page_download_task, i, r)
                fut.add_done_callback(partial(self.page_download_finish,
                                              bar, files))
                futures.append(fut)
            concurrent.futures.wait(futures)
            self.create_zip(files)

    def from_url(url):
        cpage = requests.get(url)
        soup = BeautifulSoup(cpage.text, config.get().html_parser)
        chap_num = soup.find_all("span", class_="CurChapter")[0].text
        iname = soup.find_all("a", class_="list-link")[0]["href"]
        series = MangaseeSeries("https://mangaseeonline.us" + iname)
        for chapter in series.chapters:
            if chapter.chapter == str(chap_num):
                return chapter
        return None
