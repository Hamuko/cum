from cum.scrapers.mangadex import MangadexSeries, MangadexChapter
from cum.scrapers.batoto import BatotoChapter, BatotoSeries
from cum.scrapers.dokireader import DokiReaderSeries, DokiReaderChapter
from cum.scrapers.dynastyscans import DynastyScansChapter, DynastyScansSeries
from cum.scrapers.madokami import MadokamiChapter, MadokamiSeries
from cum.scrapers.yuriism import YuriismChapter, YuriismSeries

series_scrapers = [
    MangadexSeries,
    BatotoSeries,
    DokiReaderSeries,
    DynastyScansSeries,
    MadokamiSeries,
    YuriismSeries
]
chapter_scrapers = [
    MangadexChapter,
    BatotoChapter,
    DokiReaderChapter,
    DynastyScansChapter,
    MadokamiChapter,
    YuriismChapter
]
