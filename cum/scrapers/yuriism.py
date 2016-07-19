from cum.scrapers.foolslide import FoOlSlideChapter, FoOlSlideSeries
import re


class YuriismSeries(FoOlSlideSeries):
    BASE_URL = 'https://www.yuri-ism.net/slide/'
    url_re = re.compile(r'https?://www\.yuri-ism\.net/slide/series/')

    def get_chapters(self):
        return super().get_chapters(YuriismChapter)


class YuriismChapter(FoOlSlideChapter):
    BASE_URL = YuriismSeries.BASE_URL
    url_re = re.compile(r'https?://www\.yuri-ism\.net/slide/read/')

    def from_url(url):
        return FoOlSlideChapter.from_url(url, YuriismSeries)
