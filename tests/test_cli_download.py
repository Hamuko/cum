from cum import config
from unittest import mock
import cumtest
import os


class TestCLIDownload(cumtest.CumCLITest):
    def test_download(self):
        CHAPTERS = [
            {'url': ('https://manga.madokami.al/Manga/G/GO/GOOD/Goodbye%2C%20'
                     'Everybody/Goodbye%2C%20Everybody%20%28Complete%29.zip'),
             'chapter': '0',
             'groups': ['Bird Collective Translations']},
            {'url': ('https://manga.madokami.al/Manga/G/GR/GREE/Green%20Beans/'
                     'Green%20Beans.zip'),
             'chapter': '0',
             'groups': ['Kotonoha']}
        ]
        FOLLOWS = [
            {'url': ('https://manga.madokami.al/Manga/G/GO/GOOD/'
                     'Goodbye%2C%20Everybody'),
             'alias': 'goodbye-everybody', 'name': 'Goodbye Everybody'},
            {'url': 'https://manga.madokami.al/Manga/G/GR/GREE/Green%20Beans',
             'alias': 'green-beans', 'name': 'Green Beans'}
        ]
        FILENAMES = [
            'Goodbye Everybody - c000 [Bird Collective Translations].zip',
            'Green Beans - c000 [Kotonoha].zip'
        ]
        MESSAGES = ['goodbye-everybody 0', 'green-beans 0']

        for index, follow in enumerate(FOLLOWS):
            series = self.create_mock_series(**follow)
            chapter = self.create_mock_chapter(**CHAPTERS[index])
            series.chapters.append(chapter)
            series.follow()
            FILENAMES[index] = os.path.join(series.name, FILENAMES[index])

        result = self.invoke('download')
        self.assertEqual(result.exit_code, 0)
        for message in MESSAGES:
            self.assertIn(message, result.output)
        for filename in FILENAMES:
            path = os.path.join(self.directory.name, filename)
            self.assertTrue(os.path.isfile(path))

    def test_download_alias(self):
        CHAPTERS = [
            {'url': ('https://manga.madokami.al/Manga/G/GO/GOOD/Goodbye%2C%20'
                     'Everybody/Goodbye%2C%20Everybody%20%28Complete%29.zip'),
             'chapter': '0',
             'groups': ['Bird Collective Translations']},
            {'url': ('https://manga.madokami.al/Manga/G/GR/GREE/Green%20Beans/'
                     'Green%20Beans.zip'),
             'chapter': '0',
             'groups': ['Kotonoha']}
        ]
        FOLLOWS = [
            {'url': ('https://manga.madokami.al/Manga/G/GO/GOOD/'
                     'Goodbye%2C%20Everybody'),
             'alias': 'goodbye-everybody', 'name': 'Goodbye, Everybody'},
            {'url': 'https://manga.madokami.al/Manga/G/GR/GREE/Green%20Beans',
             'alias': 'green-beans', 'name': 'Green Beans'}
        ]
        FILENAME = 'Green Beans/Green Beans - c000 [Kotonoha].zip'
        MESSAGE = 'green-beans 0'
        NOT_MESSAGE = 'goodbye-body 0'

        for index, follow in enumerate(FOLLOWS):
            series = self.create_mock_series(**follow)
            chapter = self.create_mock_chapter(**CHAPTERS[index])
            series.chapters.append(chapter)
            series.follow()

        result = self.invoke('download', 'green-beans')
        path = os.path.join(self.directory.name, FILENAME)
        self.assertEqual(result.exit_code, 0)
        self.assertIn(MESSAGE, result.output)
        self.assertNotIn(NOT_MESSAGE, result.output)
        self.assertTrue(os.path.isfile(path))

    def test_download_dokireader(self):
        CHAPTER = {'url': 'https://kobato.hologfx.com/reader/read/'
                          'sorairo_waterblue/en/0/1',
                   'chapter': '1', 'api_id': '88', 'groups': ['Doki Fansubs']}
        FOLLOW = {'url': 'https://kobato.hologfx.com/reader/series/'
                         'sorairo_waterblue/',
                  'name': 'Sorairo Waterblue',
                  'alias': 'sorairo-waterblue'}
        MESSAGE = 'sorairo-waterblue 1'
        FILENAME = '{0}/{0} - c001 [Doki Fansubs].zip'.format(FOLLOW['name'])

        series = self.create_mock_series(**FOLLOW)
        chapter = self.create_mock_chapter(**CHAPTER)
        series.chapters.append(chapter)
        series.follow()

        path = os.path.join(self.directory.name, FILENAME)
        result = self.invoke('download')
        self.assertEqual(result.exit_code, 0)
        self.assertIn(MESSAGE, result.output)
        self.assertTrue(os.path.isfile(path))

    def test_download_invalid_login(self):
        CHAPTER = {'url': 'https://manga.madokami.al/Manga/Oneshots/100%20'
                          'Dollar%20wa%20Yasu%20Sugiru/100%24%20is%20Too%20'
                          'Cheap%20%5BYAMAMOTO%20Kazune%5D%20-%20000%20%5B'
                          'Oneshot%5D%20%5BPeebs%5D.zip',
                   'chapter': '000 [Oneshot]'}
        FOLLOW = {'url': 'https://manga.madokami.al/Manga/Oneshots/100%20'
                         'Dollar%20wa%20Yasu%20Sugiru',
                  'name': '100 Dollar wa Yasu Sugiru',
                  'alias': '100-dollar-wa-yasu-sugiru'}
        MESSAGE = ('Could not download 100-dollar-wa-yasu-sugiru 000 '
                   '[Oneshot]: Madokami login error')

        series = self.create_mock_series(**FOLLOW)
        chapter = self.create_mock_chapter(**CHAPTER)
        series.chapters.append(chapter)
        series.follow()

        config.get().madokami.password = '12345'
        config.get().madokami.username = 'KoalaBeer'
        config.get().write()

        result = self.invoke('download')
        self.assertEqual(result.exit_code, 0)
        self.assertIn(MESSAGE, result.output)

    def test_download_overwriting(self):
        CHAPTERS = [
            {'url': ('https://manga.madokami.al/Manga/B/BO/BOKU/Boku%20no%20'
                     'Hero%20Academia/Boku%20no%20Hero%20Academia%20-%20c148'
                     '%20%28mag%29%20%5BFallen%20Angels%5D.zip'),
             'chapter': '148', 'groups': ['Test']},
            {'url': ('https://manga.madokami.al/Manga/B/BO/BOKU/Boku%20no%20'
                     'Hero%20Academia/Boku%20no%20Hero%20Academia%20-%20c148'
                     '%20%28mag%29%20%5BMangaStream%5D.zip'),
             'chapter': '148', 'groups': ['Test']},
        ]
        FOLLOW = {'url': ('https://manga.madokami.al/Manga/B/BO/BOKU/Boku%20no'
                          '%20Hero%20Academia'),
                  'name': 'Boku no Hero Academia',
                  'alias': 'boku-no-hero-academia'}
        FILENAMES = ['Boku no Hero Academia - c148 [Test].zip',
                     'Boku no Hero Academia - c148 [Test]-2.zip']

        series = self.create_mock_series(**FOLLOW)
        for chapter in CHAPTERS:
            chapter = self.create_mock_chapter(**chapter)
            series.chapters.append(chapter)
        series.follow()

        result = self.invoke('download')
        self.assertEqual(result.exit_code, 0)
        # print(os.listdir(self.directory.name))
        for filename in FILENAMES:
            path = os.path.join(self.directory.name, 'Boku no Hero Academia',
                                filename)
            self.assertTrue(os.path.isfile(path))

    def test_download_removed(self):
        CHAPTER = {
            'url': 'https://dynasty-scans.com/chapters/slow_start_ch404',
            'chapter': '404',
            'groups': ['/u/']
        }
        FOLLOW = {
            'url': 'https://dynasty-scans.com/series/slow_start',
            'alias': 'slow-start',
            'name': 'Slow Start'
        }
        MESSAGE = 'Removing Slow Start 404: missing from remote'

        series = self.create_mock_series(**FOLLOW)
        chapter = self.create_mock_chapter(**CHAPTER)
        series.chapters.append(chapter)
        series.follow()

        result = self.invoke('download')
        self.assertEqual(result.exit_code, 0)
        self.assertIn(MESSAGE, result.output)

        chapters = self.db.session.query(self.db.Chapter).all()
        self.assertEqual(len(chapters), 0)
