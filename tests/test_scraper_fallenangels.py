from cum import exceptions
from cumtest import CumTest
import os
import zipfile


class TestDokiReader(CumTest):
    def setUp(self):
        super().setUp()
        global fallenangels
        from cum.scrapers import fallenangels

    def test_chapter_hero_academia_49_5(self):
        URL = 'http://manga.famatg.com/read/my_hero_academia/en/0/49/5/page/1'
        URL_SHORT = 'http://manga.famatg.com/read/my_hero_academia/en/0/49/5/'
        ALIAS = 'my-hero-academia'
        NAME = 'My Hero Academia'
        chapter = fallenangels.FallenAngelsChapter.from_url(URL)
        self.assertEqual(chapter.alias, ALIAS)
        self.assertTrue(chapter.available())
        self.assertEqual(chapter.chapter, '49.5')
        self.assertIs(chapter.directory, None)
        self.assertEqual(chapter.groups, ['Fallen Angels'])
        self.assertEqual(chapter.name, NAME)
        self.assertEqual(chapter.url, URL_SHORT)
        path = os.path.join(self.directory.name, NAME,
                            'My Hero Academia - c049 x5 [Fallen Angels].zip')
        self.assertEqual(chapter.filename, path)
        chapter.download()
        self.assertTrue(os.path.isfile(path))
        with zipfile.ZipFile(path) as chapter_zip:
            files = chapter_zip.infolist()
            self.assertEqual(len(files), 3)

    def test_series_invalid(self):
        URL = 'http://manga.famatg.com/series/not_a_manga/'
        with self.assertRaises(exceptions.ScrapingError):
            series = fallenangels.FallenAngelsSeries(URL)

    def test_series_koi_x_kagi(self):
        ALIAS = 'to-love-ru-darkness'
        CHAPTERS = ['61', '62']
        GROUPS = ['Fallen Angels']
        NAME = 'To Love-Ru Darkness'
        URL = 'http://manga.famatg.com/series/to_loveru_darkness/'
        series = fallenangels.FallenAngelsSeries(URL)
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
