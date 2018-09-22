from cum.scrapers.dokireader import DokiReaderSeries, DokiReaderChapter
from cum.scrapers.dynastyscans import DynastyScansChapter, DynastyScansSeries
from cum.scrapers.madokami import MadokamiChapter, MadokamiSeries
from cum.scrapers.mangadex import MangadexSeries, MangadexChapter
from cum.scrapers.yuriism import YuriismChapter, YuriismSeries

series_scrapers = [
    DokiReaderSeries,
    DynastyScansSeries,
    MadokamiSeries,
    MangadexSeries,
    YuriismSeries,
]
chapter_scrapers = [
    DokiReaderChapter,
    DynastyScansChapter,
    MadokamiChapter,
    MangadexChapter,
    YuriismChapter,
]
