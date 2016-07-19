from cum.scrapers.foolslide import FoOlSlideChapter, FoOlSlideSeries
import re


class YuriismSeries(FoOlSlideSeries):
    url_re = re.compile(r'https?://www\.yuri-ism\.net/slide/series/')

    @property
    def BASE_URL(self):
        if self.use_https:
            return 'https://www.yuri-ism.net/slide/'
        else:
            return 'http://www.yuri-ism.net/slide/'

    def get_chapters(self):
        return super().get_chapters(YuriismChapter)


class YuriismChapter(FoOlSlideChapter):
    BASE_URL = YuriismSeries.BASE_URL
    url_re = re.compile(r'https?://www\.yuri-ism\.net/slide/read/')

    def from_url(url):
        return FoOlSlideChapter.from_url(url, YuriismSeries)
