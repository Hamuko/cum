from bs4 import BeautifulSoup
from cum import config, exceptions, output
from cum.scrapers.base import BaseChapter, BaseSeries, download_pool
from functools import partial
from jsbeautifier import beautify
from json import loads
import concurrent.futures
import re
import requests

# as of 2020/04/04, the old mobile interface which allowed easy scraping
# has been removed, and mobile now copies desktop which is protected
# by Cloudflare's Bot Management
# https://www.cloudflare.com/products/bot-management/
# in my personal testing, the following heuristic headers do reliably bypass
# it, at least to the extent necessary to hit their new progressive page load system
# however, because it is a heuristic-based system, there is no guarantee
# that just because it works from one machine and/or network location
# that it will work for others.
# feedback is appreciated.
chrome_headers = {
                    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
                    "accept-language": "en-US,en;q=0.9",
                    "upgrade-insecure-requests": "1",
                    "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.162 Safari/537.36"
                 }

class MangahereSeries(BaseSeries):
    url_re = re.compile(r'https?://((www|m)\.)?mangahere\.cc/manga/.+')

    def __init__(self, url, **kwargs):
        super().__init__(url, **kwargs)
        # convert desktop link to mobile
        # bypasses adult content warning js
        spage = requests.get(url.replace("m.", "www."), cookies = { "isAdult": "1" })
        if spage.status_code == 404:
            raise exceptions.ScrapingError
        self.soup = BeautifulSoup(spage.text, config.get().html_parser)
        self.chapters = self.get_chapters()

    def get_chapters(self):
        try:
            # broken 2020/04/04
            # rows = self.soup.find("div", class_="manga-chapters")\
                # .find("ul").find_all("li")
            rows = self.soup.find("ul", class_="detail-main-list")\
                        .find_all("a")
        except AttributeError:
            raise exceptions.ScrapingError()
        chapters = []
        for i, row in enumerate(rows):
            chap_num = re.match((r"/manga/[^/]+(?:(?:/v[0-9]+)?"
                                r"/c([0-9\.]+))/[0-9]+\.html$"),
                                row.get("href")).groups()[0]\
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
            chap_url = "https://www.mangahere.cc" + row.get("href")\
                .replace("/roll_manga/", "/manga/")
            chap_name = row.find("p").text
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
            return re.match(r"(.+) Manga - Read .+ Online at MangaHere",
                            self.soup.find("title").text).groups()[0]
        except AttributeError:
            raise exceptions.ScrapingError


class MangahereChapter(BaseChapter):
    url_re = re.compile((r'https?://((www|m)\.)?mangahere\.cc'
                        r'/(roll_)?manga/[^/]+(/v[0-9]+)?/c[0-9\.]+/[0-9]+\.html$'))
    upload_date = None
    uses_pages = True

    def _request_pages(self, mid, cid, pages):
        base_url = re.search(r"(.+/)[0-9]\.html", self.url.replace("m.", "www.")).groups()[0]
        data_url = base_url + "chapterfun.ashx?cid=" + str(cid) + "&page=" + str(len(pages) + 1) + "&key="
        chrome_headers["accept"] = "*/*"
        chrome_headers["referer"] = self.url.replace("m.", "www.")
        chrome_headers["x-requested-with"] = "XMLHttpRequest"
        data = self.session.get(data_url, headers = chrome_headers)
        if data.text == "":
            raise cum.exceptions.ScrapingError
        try:
            data_clean = beautify(data.text)
            if not getattr(self, "pvalue", None):
                self.pvalue = "https:" + re.search(r"pvalue\[i\] = \"(.+)\" \+ pvalue\[i\];", data_clean).groups()[0]
            # formatted_chap_num = re.search(r".+/c([0-9\.]+)/[0-9]\.html", self.url).groups()[0]
            # if "." not in formatted_chap_num:
                # formatted_chap_num += ".0"
            for page in loads(re.search("var pvalue = (.+);", data_clean).groups()[0]):
                full_page = self.pvalue + page
                if full_page not in pages:
                    pages.append(full_page)
        except Exception:
            raise exceptions.ScrapingError
        return pages

    def download(self):

        self.session = requests.Session()

        if not getattr(self, "cpage", None):
            self.cpage = self.session.get(self.url.replace("m.", "www."), headers = chrome_headers)
            if self.cpage.status_code == 404:
                raise exceptions.ScrapingError

        if not getattr(self, "soup", None):
            self.soup = BeautifulSoup(self.cpage.text,
                                      config.get().html_parser)

        # broken 2020/04/04
        # image_list = self.soup.find("div", class_="mangaread-img")\
            # .find_all("img")
        # pages = []
        # for image in image_list:
            # pages.append(image["data-original"].replace("http://", "https://"))

        pages = []
        (mid, cid) = (None, None)
        # index of script with ids may vary
        # it may also change as ads are added/removed from the site
        for f in range(0, len(self.soup.find_all("script"))):
            try:
                mid = re.search("var comicid = ([0-9]+)", self.soup.find_all("script")[f].text).groups()[0]
                cid = re.search("var chapterid =([0-9]+)", self.soup.find_all("script")[f].text).groups()[0]
            except AttributeError:
                pass
        if mid and cid:
            old_num_pages = -1
            while old_num_pages != len(pages):
                old_num_pages = len(pages)
                pages = self._request_pages(mid, cid, pages)
        else:
            # some titles (seems to be ones with low page counts like webtoons)
            # don't use progressively-loaded pages.  for these, the image list
            # can be extracted directly off the main page
            for g in range(0, len(self.soup.find_all("script"))):
                try:
                    pages = loads(re.search("var newImgs = (.+);var newImginfos", beautify(self.soup.find_all("script")[g].text).replace("\\", "").replace("'", "\"")).groups()[0])
                except AttributeError:
                    pass
            if not len(pages):
                raise ScrapingError
            for i, page in enumerate(pages):
                pages[i] = "https:" + page

        futures = []
        files = [None] * len(pages)
        with self.progress_bar(pages) as bar:
            for i, page in enumerate(pages):
                retries = 0
                while retries < 10:
                    try:
                        r = self.session.get(page, stream=True)
                        break
                    except requests.exceptions.ConnectionError:
                        retries += 1
                # end of chapter detection in the web ui is done by issuing requests
                # for nonexistent pages which return 404s (who comes up with this)
                if r.status_code != 404:
                    if r.status_code != 200:
                        r.close()
                        output.error("Page download got status code {}".format(str(r.status_code)))
                        raise exceptions.ScrapingError
                    fut = download_pool.submit(self.page_download_task, i, r)
                    fut.add_done_callback(partial(self.page_download_finish,
                                                bar, files))
                    futures.append(fut)
                else:
                    try:
                        del files[i]
                    except IndexError:
                        self.session.close()
                        raise exceptions.ScrapingError
            concurrent.futures.wait(futures)
            self.create_zip(files)
        self.session.close()

    def from_url(url):
        chap_num = re.match((r"https?://(?:(?:www|m)\.)?mangahere\.cc/(?:roll_)?"
                             r"manga/[^/]+(?:(?:/v[0-9]+)?/c([0-9\.]+))"
                             r"/[0-9]+\.html"), url)\
            .groups()[0]
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

    def available(self):
        if not getattr(self, "cpage", None):
            self.cpage = requests.get(self.url.replace("m.", "www."))
        return self.cpage.status_code == 200
