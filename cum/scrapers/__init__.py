from cum.scrapers.batoto import BatotoChapter, BatotoSeries
from cum.scrapers.dokireader import DokiReaderSeries, DokiReaderChapter
from cum.scrapers.dynastyscans import DynastyScansChapter, DynastyScansSeries
from cum.scrapers.fallenangels import FallenAngelsChapter, FallenAngelsSeries
from cum.scrapers.madokami import MadokamiChapter, MadokamiSeries
from cum.scrapers.yuriism import YuriismChapter, YuriismSeries

series_scrapers = [
    BatotoSeries,
    DokiReaderSeries,
    DynastyScansSeries,
    FallenAngelsSeries,
    MadokamiSeries,
    YuriismSeries
]
chapter_scrapers = [
    BatotoChapter,
    DokiReaderChapter,
    DynastyScansChapter,
    FallenAngelsChapter,
    MadokamiChapter,
    YuriismChapter
]
