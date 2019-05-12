from cum import exceptions
from cumtest import CumTest
import os
import zipfile


class TestMangaKakalot(CumTest):
    def setUp(self):
        super().setUp()
        global mangakakalot
        from cum.scrapers import mangakakalot

    def test_chapter_bonnouji_2(self):
        URL = 'https://mangakakalot.com/chapter/bonnouji/chapter_2'
        ALIAS = 'bonnouji'
        NAME = 'Bonnouji'
        chapter = mangakakalot.MangaKakalotChapter.from_url(URL)
        self.assertEqual(chapter.alias, ALIAS)
        self.assertTrue(chapter.available())
        self.assertEqual(chapter.chapter, '2')
        self.assertIs(chapter.directory, None)
        self.assertEqual(chapter.name, NAME)
        path = os.path.join(self.directory.name, NAME,
                            'Bonnouji - c002 [Unknown].zip')
        self.assertEqual(chapter.filename, path)
        chapter.download()
        self.assertTrue(os.path.isfile(path))
        with zipfile.ZipFile(path) as chapter_zip:
            files = chapter_zip.infolist()
            self.assertEqual(len(files), 21)

    def test_chapter_unavailable(self):
        URL = 'https://mangakakalot.com/chapter/dk918935/chapter_' \
              '9999999999999999999999999999999999999999999999'
        chapter = mangakakalot.MangaKakalotChapter(url=URL)
        self.assertFalse(chapter.available())

    def test_series_invalid(self):
        URL = 'https://mangakakalot.com/manga/not_a_manga/'
        with self.assertRaises(exceptions.ScrapingError):
            series = mangakakalot.MangaKakalotSeries(URL)

    def test_series_kiss_and_harmony(self):
        ALIAS = 'kiss--harmony'
        CHAPTERS = ['0.1', '0.2', '0.3', '0.4', '0.5']
        NAME = 'Kiss & Harmony'
        URL = 'https://mangakakalot.com/manga/dk918935'
        series = mangakakalot.MangaKakalotSeries(URL)
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
            self.assertIs(chapter.directory, None)
        self.assertEqual(len(CHAPTERS), 0)
