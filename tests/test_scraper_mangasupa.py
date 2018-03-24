from cum import exceptions
from cumtest import CumTest
import os
import zipfile


class TestMangaSupa(CumTest):
    def setUp(self):
        super().setUp()
        global mangasupa
        from cum.scrapers import mangasupa

    def test_chapter_technobreak_company_1(self):
        URL = 'http://mangasupa.com/chapter/rewrite/chapter_1'
        ALIAS = 'rewrite'
        NAME = 'Rewrite'
        chapter = mangasupa.MangaSupaChapter.from_url(URL)
        self.assertEqual(chapter.alias, ALIAS)
        self.assertTrue(chapter.available())
        self.assertEqual(chapter.chapter, '1')
        self.assertIs(chapter.directory, None)
        self.assertEqual(chapter.name, NAME)
        self.assertEqual(chapter.url, URL)
        path = os.path.join(self.directory.name, NAME,
                            'Rewrite - c001 [Unknown].zip')
        self.assertEqual(chapter.filename, path)
        chapter.download()
        self.assertTrue(os.path.isfile(path))
        with zipfile.ZipFile(path) as chapter_zip:
            files = chapter_zip.infolist()
            self.assertEqual(len(files), 26)

    def test_series_invalid(self):
        URL = 'http://mangasupa.com/manga/nosuchthing/'
        with self.assertRaises(exceptions.ScrapingError):
            series = mangasupa.MangaSupaSeries(URL)

    def test_series_koi_x_kagi(self):
        ALIAS = 'koi-x-kagi'
        CHAPTERS = [
            "Extra Story arc",
            "Koi x Kagi (2)",
            "Koi x Kagi (1)",
        ]
        NAME = 'Koi X Kagi'
        URL = 'http://mangasupa.com/manga/koi_x_kagi'
        series = mangasupa.MangaSupaSeries(URL)
        self.assertEqual(series.name, NAME)
        self.assertEqual(series.alias, ALIAS)
        self.assertEqual(series.url, URL)
        self.assertIs(series.directory, None)
        self.assertGreater(len(series.chapters), len(CHAPTERS))
        for chapter in series.chapters[0:len(CHAPTERS)]:
            self.assertEqual(chapter.name, NAME)
            self.assertEqual(chapter.alias, ALIAS)
            self.assertIn(chapter.title, CHAPTERS)
            self.assertIs(chapter.directory, None)
