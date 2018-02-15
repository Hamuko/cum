from cum import config
from unittest import mock
import cumtest
import os


class TestCLIFollow(cumtest.CumCLITest):
    def test_follow_dokireader(self):
        URL = 'https://kobato.hologfx.com/reader/series/new_game/'
        MESSAGE = 'Adding follow for New Game! (new-game)'

        result = self.invoke('follow', URL)
        self.assertEqual(result.exit_code, 0)
        self.assertIn(MESSAGE, result.output)

    def test_follow_dokireader_download(self):
        URL = ('https://kobato.hologfx.com/reader/series/'
               'rem_kara_hajimeru_isei_kouyuu/')
        FILENAMES = ['Rem kara Hajimeru Isei Kouyuu - c001 [Doki Fansubs].zip']
        MESSAGES = ['Adding follow for Rem kara Hajimeru Isei Kouyuu '
                    '(rem-kara-hajimeru-isei-kouyuu)',
                    'Downloading 1 chapter']

        result = self.invoke('follow', URL, '--download')
        files = [os.path.join(self.directory.name,
                              'Rem kara Hajimeru Isei Kouyuu', x)
                 for x in FILENAMES]
        self.assertEqual(result.exit_code, 0)
        for message in MESSAGES:
            self.assertIn(message, result.output)
        for file in files:
            self.assertTrue(os.path.isfile(file))

    def test_follow_dokireader_ignore(self):
        URL = ('https://kobato.hologfx.com/reader/series/'
               'rem_kara_hajimeru_isei_kouyuu/')
        MESSAGES = ['Adding follow for Rem kara Hajimeru Isei Kouyuu '
                    '(rem-kara-hajimeru-isei-kouyuu)',
                    'Ignoring 1 chapter']

        result = self.invoke('follow', URL, '--ignore')
        chapters = self.db.session.query(self.db.Chapter).all()
        self.assertEqual(result.exit_code, 0)
        for message in MESSAGES:
            self.assertIn(message, result.output)
        for chapter in chapters:
            self.assertEqual(chapter.downloaded, -1)

    def test_follow_dynastyscans(self):
        URL = 'http://dynasty-scans.com/series/akuma_no_riddle'
        MESSAGE = 'Adding follow for Akuma no Riddle (akuma-no-riddle)'

        result = self.invoke('follow', URL)
        self.assertEqual(result.exit_code, 0)
        self.assertIn(MESSAGE, result.output)

    def test_follow_dynastyscans_duplicate(self):
        FOLLOW = {'url': 'http://dynasty-scans.com/series/akuma_no_riddle',
                  'alias': 'akuma-no-riddle', 'name': 'Akuma no Riddle'}
        MESSAGES = ('You are already following Akuma no Riddle '
                    '(akuma-no-riddle)')

        series = self.create_mock_series(**FOLLOW)
        series.follow()

        result = self.invoke('follow', FOLLOW['url'])
        self.assertEqual(result.exit_code, 0)
        for message in MESSAGES:
            self.assertIn(message, result.output)

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

    @cumtest.skipIfNoMadokamiLogin
    def test_follow_non_unique_alias(self):
        URLS = ['https://kobato.hologfx.com/reader/series/new_game/',
                'https://manga.madokami.al/Manga/N/NE/NEW_/New%20Game%21']
        ALIASES = ['new-game', 'new-game-1']
        MESSAGES = ['Adding follow for New Game! (new-game)',
                    'Adding follow for New Game! (new-game-1)']

        for index in range(len(URLS)):
            result = self.invoke('follow', URLS[index])
            self.assertEqual(result.exit_code, 0)
            self.assertIn(MESSAGES[index], result.output)

        follows = self.db.session.query(self.db.Series).all()
        self.assertEqual(len(follows), len(URLS))
        for alias in ALIASES:
            self.assertIn(alias, [x.alias for x in follows])

    @cumtest.skipIfNoMadokamiLogin
    def test_follow_non_unique_alias_with_unfollow(self):
        URLS = ['https://kobato.hologfx.com/reader/series/new_game/',
                'https://manga.madokami.al/Manga/N/NE/NEW_/New%20Game%21']
        ALIASES = ['new-game', 'new-game-1']
        MESSAGE = 'Adding follow for New Game! (new-game)'

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

    def test_follow_yuriism(self):
        URL = 'http://www.yuri-ism.net/slide/series/granblue_fantasy/'
        MESSAGE = 'Adding follow for Granblue Fantasy (granblue-fantasy)'

        result = self.invoke('follow', URL)
        self.assertEqual(result.exit_code, 0)
        self.assertIn(MESSAGE, result.output)

    def test_follow_yuriism_refollow_with_directory(self):
        URL = 'http://www.yuri-ism.net/slide/series/granblue_fantasy/'
        DIRECTORY1 = 'olddirectory'
        DIRECTORY2 = 'newdirectory'

        result = self.invoke('follow', '--directory', DIRECTORY1, URL)
        series = self.db.session.query(self.db.Series).one()
        self.assertEqual(result.exit_code, 0)
        self.assertTrue(series.following)
        self.assertEqual(series.directory, DIRECTORY1)

        result = self.invoke('unfollow', 'granblue-fantasy')
        series = self.db.session.query(self.db.Series).one()
        self.assertEqual(result.exit_code, 0)
        self.assertFalse(series.following)

        result = self.invoke('follow', '--directory', DIRECTORY2, URL)
        series = self.db.session.query(self.db.Series).one()
        self.assertEqual(result.exit_code, 0)
        self.assertTrue(series.following)
        self.assertEqual(series.directory, DIRECTORY2)
