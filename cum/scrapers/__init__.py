from cum.scrapers.dokireader import DokiReaderSeries, DokiReaderChapter
from cum.scrapers.dynastyscans import DynastyScansChapter, DynastyScansSeries
from cum.scrapers.madokami import MadokamiChapter, MadokamiSeries
from cum.scrapers.mangadex import MangadexSeries, MangadexChapter
from cum.scrapers.mangasee import MangaseeSeries, MangaseeChapter
from cum.scrapers.mangahere import MangahereSeries, MangahereChapter
from cum.scrapers.yuriism import YuriismChapter, YuriismSeries

series_scrapers = [
    DokiReaderSeries,
    DynastyScansSeries,
    MadokamiSeries,
    MangadexSeries,
    MangaseeSeries,
    MangahereSeries,
    YuriismSeries,
]
chapter_scrapers = [
    DokiReaderChapter,
    DynastyScansChapter,
    MadokamiChapter,
    MangadexChapter,
    MangaseeChapter,
    MangahereChapter,
    YuriismChapter,
]
