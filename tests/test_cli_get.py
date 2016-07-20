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

    def test_get_alias_batoto(self):
        CHAPTER = {'url': 'http://bato.to/reader#350d13938df0a8c4',
                   'chapter': '0', 'groups': ['Kotonoha']}
        FOLLOW = {'url': 'http://bato.to/comic/_/comics/green-beans-r15344',
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

    @cumtest.skipIfNoBatotoLogin
    def test_get_alias_chapter_batoto(self):
        CHAPTER = {'url': 'http://bato.to/reader#5822e2f0b9beee46',
                   'chapter': '5', 'groups': ['Underdog Scans']}
        FOLLOW = {'url': 'http://bato.to/comic/_/comics/girls-go-around-r9856',
                  'alias': 'girls-go-around', 'name': 'Girls Go Around'}
        MESSAGE = 'girls-go-around 5'

        series = self.create_mock_series(**FOLLOW)
        chapter = self.create_mock_chapter(**CHAPTER)
        series.chapters.append(chapter)
        series.follow()
        path = os.path.join(self.directory.name, 'Girls Go Around',
                            'Girls Go Around - c005 [Underdog Scans].zip')

        result = self.invoke('get', 'girls-go-around:5')
        self.assertEqual(result.exit_code, 0)
        self.assertIn(MESSAGE, result.output)
        self.assertTrue(os.path.isfile(path))

    @cumtest.skipIfNoBatotoLogin
    def test_get_chapter_batoto(self):
        URL = 'http://bato.to/reader#cf03b01bd9e90ba8'
        MESSAGE = 'tomo-chan-wa-onna-no-ko 1-10'

        path = os.path.join(
            self.directory.name, 'Tomo-chan wa Onna no ko',
            'Tomo-chan wa Onna no ko - c001-010 [MSTERSCANZ].zip'
        )
        result = self.invoke('get', URL)
        self.assertEqual(result.exit_code, 0)
        self.assertIn(MESSAGE, result.output)
        self.assertTrue(os.path.isfile(path))

    @cumtest.skipIfNoBatotoLogin
    def test_get_chapter_batoto_directory(self):
        URL = 'http://bato.to/reader#cf03b01bd9e90ba8'
        DIRECTORY = 'tomochan'

        path = os.path.join(
            self.directory.name, DIRECTORY,
            'Tomo-chan wa Onna no ko - c001-010 [MSTERSCANZ].zip'
        )
        result = self.invoke('get', '--directory', DIRECTORY, URL)
        self.assertEqual(result.exit_code, 0)
        self.assertTrue(os.path.isfile(path))

    def test_get_chapter_batoto_invalid_login(self):
        URL = 'http://bato.to/reader#f0fbe77dbcc60780'
        MESSAGES = ['Batoto username:',
                    'Batoto password:',
                    'Batoto login error ({})'.format(URL)]

        config.get().batoto.username = None
        config.get().batoto.password = None
        config.get().write()

        result = self.invoke('get', URL, input='a\na')
        for message in MESSAGES:
            self.assertIn(message, result.output)

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

    @cumtest.skipIfNoBatotoLogin
    def test_get_series_batoto(self):
        URL = 'http://bato.to/comic/_/comics/akuma-to-candy-r9170'
        FILENAMES = ['Akuma to Candy - c001 [Dazzling Scans].zip',
                     'Akuma to Candy - c002 [Dazzling Scans].zip',
                     'Akuma to Candy - c003 [Dazzling Scans].zip']
        MESSAGES = ['akuma-to-candy 1', 'akuma-to-candy 2', 'akuma-to-candy 3']

        files = [os.path.join(self.directory.name, 'Akuma to Candy', x)
                 for x in FILENAMES]
        result = self.invoke('get', URL)
        self.assertEqual(result.exit_code, 0)
        for message in MESSAGES:
            self.assertIn(message, result.output)
        for file in files:
            self.assertTrue(os.path.isfile(file))

    def test_get_series_batoto_invalid_login(self):
        URL = 'http://bato.to/comic/_/comics/gekkou-spice-r2863'
        MESSAGE = 'Batoto login error ({})'.format(URL)

        config.get().batoto.password = 'Password1'
        config.get().batoto.username = 'Username1'
        config.get().write()

        result = self.invoke('get', URL)
        self.assertEqual(result.exit_code, 0)
        self.assertIn(MESSAGE, result.output)
