from cum import exceptions, output
from cum.scrapers import chapter_scrapers, series_scrapers
import re


def chapter_by_url(url):
    """Helper function used in the main cum file. Returns an appropriate Series
    class for the given URL.
    """
    for Chapter in chapter_scrapers:
        if re.match(Chapter.url_re, url):
            try:
                return Chapter.from_url(url)
            except exceptions.ScrapingError as error:
                output.warning('Scraping error ({})'.format(error.message))
                return None


def series_by_url(url):
    """Helper function used in the main cum file. Returns an appropriate Series
    object for the given URL.
    """
    for Series in series_scrapers:
        if re.match(Series.url_re, url):
            return Series(url)
