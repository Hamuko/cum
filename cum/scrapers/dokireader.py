from cum.scrapers.foolslide import FoOlSlideChapter, FoOlSlideSeries
import re


class DokiReaderSeries(FoOlSlideSeries):
    BASE_URL = "https://kobato.hologfx.com/reader/"
    url_re = re.compile(r'https?://kobato\.hologfx\.com/reader/series/')

    def get_chapters(self):
        return super().get_chapters(DokiReaderChapter)


class DokiReaderChapter(FoOlSlideChapter):
    BASE_URL = DokiReaderSeries.BASE_URL
    url_re = re.compile(r'https?://kobato\.hologfx\.com/reader/read/')

    def from_url(url):
        return FoOlSlideChapter.from_url(url, DokiReaderSeries)
