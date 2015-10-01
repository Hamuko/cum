from cum.scrapers.batoto import BatotoChapter, BatotoSeries
from cum.scrapers.dynastyscans import DynastyScansChapter, DynastyScansSeries
from cum.scrapers.madokami import MadokamiChapter, MadokamiSeries
import re

series_scrapers = [BatotoSeries, DynastyScansSeries, MadokamiSeries]
chapter_scrapers = [BatotoChapter, DynastyScansChapter, MadokamiChapter]


def chapter_by_url(url):
    """Helper function used in the main cum file. Returns an appropriate Series
    class for the given URL.
    """
    for Chapter in chapter_scrapers:
        if re.match(Chapter.url_re, url):
            return Chapter.from_url(url)


def series_by_url(url):
    """Helper function used in the main cum file. Returns an appropriate Series
    object for the given URL.
    """
    for Series in series_scrapers:
        if re.match(Series.url_re, url):
            return Series(url)
