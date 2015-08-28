from cum.scrapers.batoto import BatotoSeries
from cum.scrapers.dynastyscans import DynastyScansSeries
from cum.scrapers.madokami import MadokamiSeries
from urllib.parse import urlparse
import click


def series_by_url(url):
    """Helper function used in the main cum file. Returns an appropriate Series
    object for the given URL.
    """
    parse = urlparse(url)

    if parse.netloc == 'bato.to':
        return BatotoSeries(url)
    elif parse.netloc == 'dynasty-scans.com':
        return DynastyScansSeries(url)
    elif parse.netloc == 'manga.madokami.com':
        return MadokamiSeries(url)
    else:
        return None
