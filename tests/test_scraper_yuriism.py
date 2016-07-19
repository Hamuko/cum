from cum import exceptions
from cumtest import CumTest
import os
import zipfile


class TestDokiReader(CumTest):
    def setUp(self):
        super().setUp()
        global yuriism
        from cum.scrapers import yuriism

    def test_chapter_kancolle_2(self):
        URL = 'http://www.yuri-ism.net/slide/read/kancolle/en/6/2/page/1'
        URL_SHORT = 'http://www.yuri-ism.net/slide/read/kancolle/en/6/2/'
        ALIAS = 'kancolle'
        NAME = 'Kancolle'
        chapter = yuriism.YuriismChapter.from_url(URL)
        self.assertEqual(chapter.alias, ALIAS)
        self.assertTrue(chapter.available())
        self.assertEqual(chapter.chapter, '2')
        self.assertIs(chapter.directory, None)
        self.assertEqual(chapter.groups, ['Yuri-ism'])
        self.assertEqual(chapter.name, NAME)
        self.assertEqual(chapter.url, URL_SHORT)
        path = os.path.join(self.directory.name, NAME,
                            'Kancolle - c002 [Yuri-ism].zip')
        self.assertEqual(chapter.filename, path)
        chapter.download()
        self.assertTrue(os.path.isfile(path))
        with zipfile.ZipFile(path) as chapter_zip:
            files = chapter_zip.infolist()
            self.assertEqual(len(files), 18)

    def test_chapter_kancolle_2_https(self):
        URL = 'https://www.yuri-ism.net/slide/read/kancolle/en/6/2/page/1'
        URL_SHORT = 'https://www.yuri-ism.net/slide/read/kancolle/en/6/2/'
        ALIAS = 'kancolle'
        NAME = 'Kancolle'
        chapter = yuriism.YuriismChapter.from_url(URL)
        self.assertEqual(chapter.alias, ALIAS)
        self.assertTrue(chapter.available())
        self.assertEqual(chapter.chapter, '2')
        self.assertIs(chapter.directory, None)
        self.assertEqual(chapter.groups, ['Yuri-ism'])
        self.assertEqual(chapter.name, NAME)
        self.assertEqual(chapter.url, URL_SHORT)
        path = os.path.join(self.directory.name, NAME,
                            'Kancolle - c002 [Yuri-ism].zip')
        self.assertEqual(chapter.filename, path)
        chapter.download()
        self.assertTrue(os.path.isfile(path))
        with zipfile.ZipFile(path) as chapter_zip:
            files = chapter_zip.infolist()
            self.assertEqual(len(files), 18)

    def test_series_invalid(self):
        URL = 'http://www.yuri-ism.net/slide/series/not_a_manga/'
        with self.assertRaises(exceptions.ScrapingError):
            series = yuriism.YuriismSeries(URL)

    def test_series_joshiraku(self):
        ALIAS = 'joshiraku'
        CHAPTERS = ['166']
        GROUPS = ['Yuri-ism']
        NAME = 'Joshiraku'
        URL = 'http://www.yuri-ism.net/slide/series/joshiraku/'
        series = yuriism.YuriismSeries(URL)
        self.assertEqual(series.name, NAME)
        self.assertEqual(series.alias, ALIAS)
        self.assertEqual(series.url, URL)
        self.assertIs(series.directory, None)
        self.assertEqual(len(series.chapters), len(CHAPTERS))
        for chapter in series.chapters:
            self.assertEqual(chapter.name, NAME)
            self.assertEqual(chapter.alias, ALIAS)
            self.assertIn(chapter.chapter, CHAPTERS)
            CHAPTERS.remove(chapter.chapter)
            for group in chapter.groups:
                self.assertIn(group, GROUPS)
            self.assertIs(chapter.directory, None)
        self.assertEqual(len(CHAPTERS), 0)

    def test_series_joshiraku_https(self):
        ALIAS = 'joshiraku'
        CHAPTERS = ['166']
        GROUPS = ['Yuri-ism']
        NAME = 'Joshiraku'
        URL = 'https://www.yuri-ism.net/slide/series/joshiraku/'
        series = yuriism.YuriismSeries(URL)
        self.assertEqual(series.name, NAME)
        self.assertEqual(series.alias, ALIAS)
        self.assertEqual(series.url, URL)
        self.assertIs(series.directory, None)
        self.assertEqual(len(series.chapters), len(CHAPTERS))
        for chapter in series.chapters:
            self.assertEqual(chapter.name, NAME)
            self.assertEqual(chapter.alias, ALIAS)
            self.assertIn(chapter.chapter, CHAPTERS)
            CHAPTERS.remove(chapter.chapter)
            for group in chapter.groups:
                self.assertIn(group, GROUPS)
            self.assertIs(chapter.directory, None)
        self.assertEqual(len(CHAPTERS), 0)
