from cum import config
from unittest import mock
import cumtest
import os


class TestCLIFollow(cumtest.CumCLITest):
    @cumtest.skipIfNoBatotoLogin
    def test_follow_batoto(self):
        URL = 'http://bato.to/comic/_/comics/akuma-no-riddle-r9759'
        MESSAGE = 'Adding follow for Akuma no Riddle (akuma-no-riddle)'

        result = self.invoke('follow', URL)
        self.assertEqual(result.exit_code, 0)
        self.assertIn(MESSAGE, result.output)

    @cumtest.skipIfNoBatotoLogin
    def test_follow_batoto_duplicate(self):
        FOLLOW = {'url': 'http://bato.to/comic/_/comics/akuma-no-riddle-r9759',
                  'alias': 'akuma-no-riddle', 'name': 'Akuma no Riddle'}
        MESSAGES = ('You are already following Akuma no Riddle '
                    '(akuma-no-riddle)')

        series = self.create_mock_series(**FOLLOW)
        series.follow()

        result = self.invoke('follow', FOLLOW['url'])
        self.assertEqual(result.exit_code, 0)
        for message in MESSAGES:
            self.assertIn(message, result.output)

    @cumtest.skipIfNoBatotoLogin
    def test_follow_batoto_download(self):
        URL = 'http://bato.to/comic/_/comics/dog-days-r6928'
        FILENAMES = ['Dog Days - c000 [CXC Scans].zip',
                     'Dog Days - c001 [CXC Scans].zip',
                     'Dog Days - c002 [CXC Scans].zip',
                     'Dog Days - c003 [CXC Scans].zip',
                     'Dog Days - c004 [CXC Scans].zip']
        MESSAGES = ['Adding follow for Dog Days (dog-days)',
                    'Downloading 5 chapters']

        result = self.invoke('follow', URL, '--download')
        files = [os.path.join(self.directory.name, 'Dog Days', x)
                 for x in FILENAMES]
        self.assertEqual(result.exit_code, 0)
        for message in MESSAGES:
            self.assertIn(message, result.output)
        for file in files:
            self.assertTrue(os.path.isfile(file))

    @cumtest.skipIfNoBatotoLogin
    def test_follow_batoto_ignore(self):
        URL = 'http://bato.to/comic/_/comics/dog-days-r6928'
        MESSAGES = ['Adding follow for Dog Days (dog-days)',
                    'Ignoring 5 chapters']

        result = self.invoke('follow', URL, '--ignore')
        chapters = self.db.session.query(self.db.Chapter).all()
        self.assertEqual(result.exit_code, 0)
        for message in MESSAGES:
            self.assertIn(message, result.output)
        for chapter in chapters:
            self.assertEqual(chapter.downloaded, -1)

    def test_follow_batoto_invalid_login(self):
        URL = 'http://bato.to/comic/_/comics/hot-road-r2243'
        MESSAGE = 'Batoto login error ({})'.format(URL)

        config.get().batoto.password = 'Notvalid'
        config.get().batoto.username = 'Notvalid'
        config.get().write()

        result = self.invoke('follow', URL)
        self.assertEqual(result.exit_code, 0)
        self.assertIn(MESSAGE, result.output)

    @cumtest.skipIfNoBatotoLogin
    def test_follow_batoto_refollow_with_directory(self):
        URL = 'http://bato.to/comic/_/comics/dog-days-r6928'
        DIRECTORY1 = 'olddirectory'
        DIRECTORY2 = 'newdirectory'

        result = self.invoke('follow', '--directory', DIRECTORY1, URL)
        series = self.db.session.query(self.db.Series).one()
        self.assertEqual(result.exit_code, 0)
        self.assertTrue(series.following)
        self.assertEqual(series.directory, DIRECTORY1)

        result = self.invoke('unfollow', 'dog-days')
        series = self.db.session.query(self.db.Series).one()
        self.assertEqual(result.exit_code, 0)
        self.assertFalse(series.following)

        result = self.invoke('follow', '--directory', DIRECTORY2, URL)
        series = self.db.session.query(self.db.Series).one()
        self.assertEqual(result.exit_code, 0)
        self.assertTrue(series.following)
        self.assertEqual(series.directory, DIRECTORY2)

    def test_follow_dynastyscans(self):
        URL = 'http://dynasty-scans.com/series/akuma_no_riddle'
        MESSAGE = 'Adding follow for Akuma no Riddle (akuma-no-riddle)'

        result = self.invoke('follow', URL)
        self.assertEqual(result.exit_code, 0)
        self.assertIn(MESSAGE, result.output)

    def test_follow_invalid(self):
        URL = 'http://www.google.com'
        MESSAGE = 'Invalid URL "{}"'.format(URL)

        result = self.invoke('follow', URL)
        self.assertEqual(result.exit_code, 0)
        self.assertIn(MESSAGE, result.output)

    @cumtest.skipIfNoMadokamiLogin
    def test_follow_madokami(self):
        URL = 'https://manga.madokami.al/Manga/A/AK/AKUM/Akuma%20no%20Riddle'
        MESSAGE = 'Adding follow for Akuma no Riddle (akuma-no-riddle)'

        result = self.invoke('follow', URL)
        self.assertEqual(result.exit_code, 0)
        self.assertIn(MESSAGE, result.output)

    def test_follow_madokami_download_invalid_login(self):
        URL = 'https://manga.madokami.al/Manga/A/AK/AKUM/Akuma%20no%20Riddle'
        MESSAGE = '==> Madokami login error (' + URL + ')'

        config.get().madokami.password = 'notworking'
        config.get().madokami.username = 'notworking'
        config.get().write()

        result = self.invoke('follow', URL, '--download')
        self.assertEqual(result.exit_code, 0)
        self.assertIn(MESSAGE, result.output)

    @cumtest.skipIfNoBatotoLogin
    @cumtest.skipIfNoMadokamiLogin
    def test_follow_non_unique_alias(self):
        URLS = ['https://bato.to/comic/_/comics/happiness-oshimi-shuzo-r14710',
                'https://manga.madokami.al/Manga/H/HA/HAPP/Happiness%20'
                '%28OSHIMI%20Shuzo%29']
        ALIASES = ['happiness-oshimi-shuzo', 'happiness-oshimi-shuzo-1']
        MESSAGES = ['Adding follow for Happiness (OSHIMI Shuzo) '
                    '(happiness-oshimi-shuzo)',
                    'Adding follow for Happiness (OSHIMI Shuzo) '
                    '(happiness-oshimi-shuzo-1)']

        for index in range(len(URLS)):
            result = self.invoke('follow', URLS[index])
            self.assertEqual(result.exit_code, 0)
            self.assertIn(MESSAGES[index], result.output)

        follows = self.db.session.query(self.db.Series).all()
        self.assertEqual(len(follows), len(URLS))
        for alias in ALIASES:
            self.assertIn(alias, [x.alias for x in follows])

    @cumtest.skipIfNoBatotoLogin
    @cumtest.skipIfNoMadokamiLogin
    def test_follow_non_unique_alias_with_unfollow(self):
        URLS = ['https://bato.to/comic/_/comics/happiness-oshimi-shuzo-r14710',
                'https://manga.madokami.al/Manga/H/HA/HAPP/Happiness%20'
                '%28OSHIMI%20Shuzo%29']
        ALIASES = ['happiness-oshimi-shuzo', 'happiness-oshimi-shuzo-1']
        MESSAGE = ('Adding follow for Happiness (OSHIMI Shuzo) '
                   '(happiness-oshimi-shuzo)')

        result = self.invoke('follow', URLS[0])
        self.assertEqual(result.exit_code, 0)
        self.assertIn(MESSAGE, result.output)

        result = self.invoke('unfollow', ALIASES[0])
        self.assertEqual(result.exit_code, 0)

        result = self.invoke('follow', URLS[1])
        self.assertEqual(result.exit_code, 0)
        self.assertIn(MESSAGE, result.output)

        follows = self.db.session.query(self.db.Series).order_by('id').all()
        self.assertEqual(len(follows), len(URLS))
        self.assertEqual(follows[0].alias, ALIASES[1])
        self.assertEqual(follows[1].alias, ALIASES[0])
