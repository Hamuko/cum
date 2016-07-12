from cum.scrapers.foolslide import FoOlSlideChapter, FoOlSlideSeries
import re


class FallenAngelsSeries(FoOlSlideSeries):
    BASE_URL = "http://manga.famatg.com/"
    url_re = re.compile(r'http://manga\.famatg\.com/series/')

    def get_chapters(self):
        return super().get_chapters(FallenAngelsChapter)


class FallenAngelsChapter(FoOlSlideChapter):
    BASE_URL = FallenAngelsSeries.BASE_URL
    url_re = re.compile(r'http://manga\.famatg\.com/read/')

    def from_url(url):
        return FoOlSlideChapter.from_url(url, FallenAngelsSeries)
