from cum import config
from cumtest import CumTest
import os
import tempfile
import unittest
import zipfile


class TestDynastyScans(CumTest):
    def setUp(self):
        super().setUp()
        global dynastyscans
        from cum.scrapers import dynastyscans

    def test_chapter_information_shikinami_doujin(self):
        ALIAS = 'a-doujin-where-shikinami-became-the-secretary-ship'
        CHAPTER = ' More! A Doujin Where Shikinami Became the Secretary Ship'
        NAME = 'A Doujin Where Shikinami Became the Secretary Ship'
        URL = ('https://dynasty-scans.com/chapters/a_doujin_where_shikinami_'
               'became_the_secretary_ship_more_a_doujin_where_shikinami_'
               'became_the_secretary_ship')
        chapter = dynastyscans.DynastyScansChapter.from_url(URL)
        self.assertEqual(chapter.alias, ALIAS)
        self.assertTrue(chapter.available())
        self.assertEqual(chapter.chapter, CHAPTER)
        self.assertEqual(chapter.groups, ['Anonymous'])
        self.assertEqual(chapter.name, NAME)
        self.assertIs(chapter.directory, None)
        self.assertEqual(chapter.url, URL)
        path = os.path.join(
            self.directory.name,
            'A Doujin Where Shikinami Became the Secretary Ship',
            'A Doujin Where Shikinami Became the Secretary Ship - c000 '
            '[ More A Doujin Where Shikinami Became the Secretary Ship] '
            '[Anonymous].zip'
        )
        self.assertEqual(chapter.filename, path)
        chapter.download()
        self.assertTrue(os.path.isfile(path))
        with zipfile.ZipFile(path) as chapter_zip:
            files = chapter_zip.infolist()
            self.assertEqual(len(files), 27)

    def test_chapter_no_series(self):
        URL = 'https://dynasty-scans.com/chapters/youre_cute'
        NAME = 'Umekichi'
        CHAPTER = "You're Cute"
        config.get().cbz = True
        chapter = dynastyscans.DynastyScansChapter.from_url(URL)
        self.assertEqual(chapter.alias, NAME.lower())
        self.assertTrue(chapter.available())
        self.assertEqual(chapter.chapter, CHAPTER)
        self.assertIs(chapter.directory, None)
        self.assertEqual(chapter.groups, ['/u/ Scanlations'])
        self.assertEqual(chapter.name, NAME)
        self.assertEqual(chapter.url, URL)
        path = os.path.join(
            self.directory.name, NAME,
            "Umekichi - c000 [You're Cute] [u Scanlations].cbz"
        )
        self.assertEqual(chapter.filename, path)
        chapter.get(use_db=False)
        self.assertTrue(os.path.isfile(path))
        with zipfile.ZipFile(path) as chapter_zip:
            files = chapter_zip.infolist()
            self.assertEqual(len(files), 23)

    def test_chapter_no_series_or_artist(self):
        URL = 'https://dynasty-scans.com/chapters/troubled_mutsuki_chan/'
        NAME = 'Troubled Mutsuki-Chan'
        chapter = dynastyscans.DynastyScansChapter.from_url(URL)
        self.assertIs(chapter.alias, None)
        self.assertTrue(chapter.available())
        self.assertEqual(chapter.chapter, '0')
        self.assertIs(chapter.directory, None)
        self.assertEqual(chapter.groups, ['Anonymous'])
        self.assertEqual(chapter.name, NAME)
        self.assertEqual(chapter.url, URL[:-1])
        path = os.path.join(self.directory.name, NAME,
                            'Troubled Mutsuki-Chan - c000 [Anonymous].zip')
        self.assertEqual(chapter.filename, path)
        chapter.download()
        self.assertTrue(os.path.isfile(path))
        with zipfile.ZipFile(path) as chapter_zip:
            files = chapter_zip.infolist()
            self.assertEqual(len(files), 8)

    def test_series_lily_love(self):
        ALIAS = 'lily-love'
        CHAPTERS = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11',
                    '12', '13', '14', '15', '16', '17', 'Special 1',
                    'Special 2', '18', '19', '20']
        URL = 'https://dynasty-scans.com/series/lily_love/'
        series = dynastyscans.DynastyScansSeries(URL)
        scraped_chapters = [x.chapter for x in series.chapters]
        for c in CHAPTERS:
            self.assertEqual(scraped_chapters.count(c), 1)
        filenames = []
        for sc in series.chapters:
            self.assertNotIn(sc.filename, filenames)
            filenames.append(sc.filename)

    def test_series_stretch(self):
        ALIAS = 'stretch'
        CHAPTERS = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10',
                    '11', '11.5', '12', '13', '14', '15', '16', '17', '18',
                    '19', '20', '21', '22', '22.1', '22.5', '23', '24', '25',
                    '26', '27', '27.1', '28', '29', '30', '31', '32', '32.5',
                    '33', '34', '35', '36', '37', '38', '39', '40', '41', '42',
                    '43', '44', '45', 'Volume 1 Extra', 'Volume 2 Extra',
                    'Volume 3 Extra', 'Volume 4 Extra']
        GROUPS = ['Boon Scanlations', 'SAZ']
        NAME = 'Stretch'
        URL = 'https://dynasty-scans.com/series/stretch'
        series = dynastyscans.DynastyScansSeries(URL)
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

if __name__ == '__main__':
    unittest.main()
