from cum import config
import os
import tempfile
import unittest
import zipfile


class TestDynastyScans(unittest.TestCase):
    def setUp(self):
        global dynastyscans
        self.directory = tempfile.TemporaryDirectory()
        config.initialize(directory=self.directory.name)
        config.get().download_directory = self.directory.name
        from cum.scrapers import dynastyscans

    def tearDown(self):
        self.directory.cleanup()

    def test_chapter_information_shikinami_doujin(self):
        ALIAS = 'a-doujin-where-shikinami-became-the-secretary-ship'
        CHAPTER = ' More! A Doujin Where Shikinami Became the Secretary Ship'
        NAME = 'A Doujin Where Shikinami Became the Secretary Ship'
        URL = ('http://dynasty-scans.com/chapters/a_doujin_where_shikinami_'
               'became_the_secretary_ship_more_a_doujin_where_shikinami_'
               'became_the_secretary_ship')
        chapter = dynastyscans.DynastyScansChapter.from_url(URL)
        assert chapter.alias == ALIAS
        assert chapter.available() is True
        assert chapter.chapter == CHAPTER
        assert chapter.groups == ['/a/nonymous']
        assert chapter.name == NAME
        assert chapter.directory is None
        assert chapter.url == URL
        path = os.path.join(
            self.directory.name,
            'A Doujin Where Shikinami Became the Secretary Ship',
            'A Doujin Where Shikinami Became the Secretary Ship - c000 '
            '[ More A Doujin Where Shikinami Became the Secretary Ship] '
            '[anonymous].zip'
        )
        assert chapter.filename == path
        chapter.download()
        assert os.path.isfile(path) is True
        with zipfile.ZipFile(path) as chapter_zip:
            files = chapter_zip.infolist()
            assert len(files) == 27

    def test_chapter_no_series(self):
        URL = 'http://dynasty-scans.com/chapters/youre_cute'
        NAME = 'Umekichi'
        CHAPTER = "You're Cute"
        config.get().cbz = True
        chapter = dynastyscans.DynastyScansChapter.from_url(URL)
        assert chapter.alias == NAME.lower()
        assert chapter.available() is True
        assert chapter.chapter == CHAPTER
        assert chapter.directory is None
        assert chapter.groups == ['/u/ Scanlations']
        assert chapter.name == NAME
        assert chapter.url == URL
        path = os.path.join(
            self.directory.name, NAME,
            "Umekichi - c000 [You're Cute] [u Scanlations].cbz"
        )
        assert chapter.filename == path
        chapter.get(use_db=False)
        assert os.path.isfile(path) is True
        with zipfile.ZipFile(path) as chapter_zip:
            files = chapter_zip.infolist()
            assert len(files) == 23

    def test_chapter_no_series_or_artist(self):
        URL = 'http://dynasty-scans.com/chapters/troubled_mutsuki_chan'
        NAME = 'Troubled Mutsuki-Chan'
        chapter = dynastyscans.DynastyScansChapter.from_url(URL)
        assert chapter.alias is None
        assert chapter.available() is True
        assert chapter.chapter == '0'
        assert chapter.directory is None
        assert chapter.groups == ['/a/nonymous']
        assert chapter.name == NAME
        assert chapter.url == URL
        path = os.path.join(self.directory.name, NAME,
                            'Troubled Mutsuki-Chan - c000 [anonymous].zip')
        assert chapter.filename == path
        chapter.download()
        assert os.path.isfile(path) is True
        with zipfile.ZipFile(path) as chapter_zip:
            files = chapter_zip.infolist()
            assert len(files) == 8

    def test_series_stretch(self):
        ALIAS = 'stretch'
        CHAPTERS = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10',
                    '11', '11.5', '12', '13', '14', '15', '16', '17', '18',
                    '19', '20', '21', '22', '22.1', '22.5', '23', '24', '25',
                    '26', '27', '27.1', '28', '29', '30', '31', '32', '32.5',
                    '33', '34', '35', '36', '37', '38', '39', '40', '41', '42',
                    '43', '44', '45', 'Volume 1 Extra', 'Volume 2 Extra',
                    'Volume 3 Extra']
        GROUPS = ['Boon Scanlations']
        NAME = 'Stretch'
        URL = 'http://dynasty-scans.com/series/stretch'
        series = dynastyscans.DynastyScansSeries(URL)
        assert series.name == NAME
        assert series.alias == ALIAS
        assert series.url == URL
        assert series.directory is None
        assert len(series.chapters) == len(CHAPTERS)
        for chapter in series.chapters:
            assert chapter.name == NAME
            assert chapter.alias == ALIAS
            assert chapter.chapter in CHAPTERS
            CHAPTERS.remove(chapter.chapter)
            for group in chapter.groups:
                assert group in GROUPS
            assert chapter.directory is None
        assert len(CHAPTERS) == 0

if __name__ == '__main__':
    unittest.main()
