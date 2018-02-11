from cum import config
from unittest import mock
import cumtest
import os


class TestCLIGet(cumtest.CumCLITest):
    def test_get_alias_invalid(self):
        MESSAGE = 'Invalid selection "alias,1"'

        result = self.invoke('get', 'alias,1')
        self.assertEqual(result.exit_code, 0)
        self.assertIn(MESSAGE, result.output)

    def test_get_alias(self):
        CHAPTER = {'url': ('https://manga.madokami.al/Manga/G/GR/GREE/Green%20'
                           'Beans/Green%20Beans.zip'),
                   'chapter': '0', 'groups': ['Kotonoha']}
        FOLLOW = {'url': ('https://manga.madokami.al/Manga/G/GR/GREE/Green%20'
                          'Beans'),
                  'alias': 'green-beans', 'name': 'Green Beans'}
        MESSAGE = 'green-beans 0'

        series = self.create_mock_series(**FOLLOW)
        chapter = self.create_mock_chapter(**CHAPTER)
        series.chapters.append(chapter)
        series.follow()
        path = os.path.join(self.directory.name, 'Green Beans',
                            'Green Beans - c000 [Kotonoha].zip')

        result = self.invoke('get', 'green-beans')
        self.assertEqual(result.exit_code, 0)
        self.assertIn(MESSAGE, result.output)
        self.assertTrue(os.path.isfile(path))

    def test_get_alias_chapter(self):
        CHAPTER = {'url': ('https://manga.madokami.al/Manga/G/GR/GREE/Green%20'
                           'Beans/Green%20Beans.zip'),
                   'chapter': '0', 'groups': ['Kotonoha']}
        FOLLOW = {'url': ('https://manga.madokami.al/Manga/G/GR/GREE/Green%20'
                          'Beans'),
                  'alias': 'green-beans', 'name': 'Green Beans'}
        MESSAGE = 'green-beans 0'

        series = self.create_mock_series(**FOLLOW)
        chapter = self.create_mock_chapter(**CHAPTER)
        series.chapters.append(chapter)
        series.follow()
        path = os.path.join(self.directory.name, 'Green Beans',
                            'Green Beans - c000 [Kotonoha].zip')

        result = self.invoke('get', 'green-beans:0')
        self.assertEqual(result.exit_code, 0)
        self.assertIn(MESSAGE, result.output)
        self.assertTrue(os.path.isfile(path))

    def test_get_chapter_madokami_directory(self):
        URL = ('https://manga.madokami.al/Manga/Oneshots/12-ji%20no%20Kane%20'
               'ga%20Naru/12%20O%27Clock%20Bell%20Rings%20%5BKISHIMOTO%20'
               'Seishi%5D%20-%20000%20%5BOneshot%5D%20%5BTurtle%20Paradise%5D'
               '.zip')
        DIRECTORY = 'oneshots'

        path = os.path.join(
            self.directory.name, DIRECTORY,
            '12-ji no Kane ga Naru - c000 [000 [Oneshot] [Turtle] [Unknown]'
            '.zip'
        )
        result = self.invoke('get', '--directory', DIRECTORY, URL)
        self.assertEqual(result.exit_code, 0)
        self.assertTrue(os.path.isfile(path))

    def test_get_chapter_madokami_invalid_login(self):
        URL = ('https://manga.madokami.al/Manga/Oneshots/12-ji%20no%20Kane%20'
               'ga%20Naru/12%20O%27Clock%20Bell%20Rings%20%5BKISHIMOTO%20'
               'Seishi%5D%20-%20000%20%5BOneshot%5D%20%5BTurtle%20Paradise%5D'
               '.zip')
        MESSAGES = ['Madokami username:',
                    'Madokami password:',
                    'Madokami login error']

        config.get().madokami.username = None
        config.get().madokami.password = None
        config.get().write()

        result = self.invoke('get', URL, input='a\na')
        for message in MESSAGES:
            self.assertIn(message, result.output)
