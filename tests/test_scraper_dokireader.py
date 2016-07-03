from cum import exceptions
from cumtest import CumTest
import os
import zipfile


class TestDokiReader(CumTest):
    def setUp(self):
        super().setUp()
        global dokireader
        from cum.scrapers import dokireader

    def test_chapter_technobreak_company_1(self):
        URL = ('https://kobato.hologfx.com/reader/read/'
               'technobreak_company/en/0/1/page/1')
        URL_SHORT = ('https://kobato.hologfx.com/reader/read/'
                     'technobreak_company/en/0/1/')
        ALIAS = 'technobreak-company'
        NAME = 'Technobreak Company'
        chapter = dokireader.DokiReaderChapter.from_url(URL)
        self.assertEqual(chapter.alias, ALIAS)
        self.assertTrue(chapter.available())
        self.assertEqual(chapter.chapter, '1')
        self.assertIs(chapter.directory, None)
        self.assertEqual(chapter.groups, ['Doki Fansubs'])
        self.assertEqual(chapter.name, NAME)
        self.assertEqual(chapter.url, URL_SHORT)
        path = os.path.join(self.directory.name, NAME,
                            'Technobreak Company - c001 [Doki Fansubs].zip')
        self.assertEqual(chapter.filename, path)
        chapter.download()
        self.assertTrue(os.path.isfile(path))
        with zipfile.ZipFile(path) as chapter_zip:
            files = chapter_zip.infolist()
            self.assertEqual(len(files), 18)

    def test_series_invalid(self):
        URL = 'https://kobato.hologfx.com/reader/series/not_a_manga/'
        with self.assertRaises(exceptions.ScrapingError):
            series = dokireader.DokiReaderSeries(URL)

    def test_series_koi_x_kagi(self):
        ALIAS = 'koi-x-kagi'
        CHAPTERS = ['1', '2', '3', '3.1', '3.2', '4',
                    '5', '6', '6.1', '6.2', '6.3']
        GROUPS = ['Doki Fansubs']
        NAME = 'Koi x Kagi'
        URL = 'https://kobato.hologfx.com/reader/series/koi_x_kagi/'
        series = dokireader.DokiReaderSeries(URL)
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
