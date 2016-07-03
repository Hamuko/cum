from cum.scrapers.batoto import BatotoChapter, BatotoSeries
from cum.scrapers.dokireader import DokiReaderSeries, DokiReaderChapter
from cum.scrapers.dynastyscans import DynastyScansChapter, DynastyScansSeries
from cum.scrapers.madokami import MadokamiChapter, MadokamiSeries

series_scrapers = [
    BatotoSeries,
    DokiReaderSeries,
    DynastyScansSeries,
    MadokamiSeries
]
chapter_scrapers = [
    BatotoChapter,
    DokiReaderChapter,
    DynastyScansChapter,
    MadokamiChapter
]
