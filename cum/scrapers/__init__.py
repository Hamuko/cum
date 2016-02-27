from cum.scrapers.batoto import BatotoChapter, BatotoSeries
from cum.scrapers.dynastyscans import DynastyScansChapter, DynastyScansSeries
from cum.scrapers.madokami import MadokamiChapter, MadokamiSeries

series_scrapers = [BatotoSeries, DynastyScansSeries, MadokamiSeries]
chapter_scrapers = [BatotoChapter, DynastyScansChapter, MadokamiChapter]
