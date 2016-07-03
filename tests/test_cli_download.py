from cum import config
from unittest import mock
import cumtest
import os


class TestCLIDownload(cumtest.CumCLITest):
    @cumtest.skipIfNoBatotoLogin
    def test_download(self):
        CHAPTERS = [
            {'url': 'http://bato.to/reader#aef716a5a8acc5a7', 'chapter': '0',
             'groups': ['Bird Collective Translations']},
            {'url': 'http://bato.to/reader#350d13938df0a8c4', 'chapter': '0',
             'groups': ['Kotonoha']}
        ]
        FOLLOWS = [
            {'url': 'http://bato.to/comic/_/comics/goodbye-body-r13725',
             'alias': 'goodbye-body', 'name': 'Goodbye Body'},
            {'url': 'http://bato.to/comic/_/comics/green-beans-r15344',
             'alias': 'green-beans', 'name': 'Green Beans'}
        ]
        FILENAMES = [
            'Goodbye Body - c000 [Bird Collective Translations].zip',
            'Green Beans - c000 [Kotonoha].zip'
        ]
        MESSAGES = ['goodbye-body 0', 'green-beans 0']

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

    @cumtest.skipIfNoBatotoLogin
    def test_download_alias(self):
        CHAPTERS = [
            {'url': 'http://bato.to/reader#aef716a5a8acc5a7', 'chapter': '0',
             'groups': ['Bird Collective Translations']},
            {'url': 'http://bato.to/reader#350d13938df0a8c4', 'chapter': '0',
             'groups': ['Kotonoha']}
        ]
        FOLLOWS = [
            {'url': 'http://bato.to/comic/_/comics/goodbye-body-r13725',
             'alias': 'goodbye-body', 'name': 'Goodbye Body'},
            {'url': 'http://bato.to/comic/_/comics/green-beans-r15344',
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

    @cumtest.skipIfNoBatotoLogin
    def test_download_removed(self):
        CHAPTER = {
            'url': 'http://bato.to/reader#ba173e587bdc9325',
            'chapter': '210'
        }
        FOLLOW = {
            'url': 'http://bato.to/comic/_/comics/tomo-chan-wa-onna-no-r15722',
            'alias': 'tomo-chan-wa-onna-no-ko',
            'name': 'Tomo-chan wa Onna no ko!'
        }
        MESSAGE = 'Removing Tomo-chan wa Onna no ko! 210: missing from remote'

        series = self.create_mock_series(**FOLLOW)
        chapter = self.create_mock_chapter(**CHAPTER)
        series.chapters.append(chapter)
        series.follow()

        result = self.invoke('download')
        chapters = (self.db.session.query(self.db.Chapter).all())
        self.assertEqual(len(chapters), 0)
        self.assertEqual(result.exit_code, 0)
        self.assertIn(MESSAGE, result.output)
