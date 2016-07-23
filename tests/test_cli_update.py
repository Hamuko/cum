from cum import config
from unittest import mock
import cumtest
import datetime


class TestCLIUpdate(cumtest.CumCLITest):
    @cumtest.skipIfNoBatotoLogin
    def test_update(self):
        FOLLOWS = [
            {'url': 'http://bato.to/comic/_/comics/femme-fatale-r468',
             'alias': 'femme-fatale', 'name': 'Femme Fatale'},
            {'url': 'http://bato.to/comic/_/comics/houkago-r9187',
             'alias': 'houkago', 'name': 'Houkago'}
        ]
        MESSAGES = [
            'Updating 2 series',
            'femme-fatale 1  2  3  4  4.5  5  6  7  8  8.5  9  10  11  12',
            'houkago      1  2'
        ]

        config.get().compact_new = True
        config.get().write()

        for follow in FOLLOWS:
            series = self.create_mock_series(**follow)
            series.follow()
        chapters = self.db.session.query(self.db.Chapter).all()
        self.assertEqual(len(chapters), 0)

        result = self.invoke('update')
        chapters = self.db.session.query(self.db.Chapter).all()
        self.assertEqual(result.exit_code, 0)
        for message in MESSAGES:
            self.assertIn(message, result.output)
        self.assertEqual(len(chapters), 16)

    def test_update_fast(self):
        CHAPTERS2 = [
            {'chapter': '1', 'url': 'http://bato.to/reader#e9df010324a94b03'},
            {'chapter': '2', 'url': 'http://bato.to/reader#6e8bf206e9f79b85'},
        ]
        CHAPTERS3 = [
            {'chapter': '0', 'url': 'http://bato.to/reader#f04036c7567ca8ab'},
            {'chapter': '1', 'url': 'http://bato.to/reader#4ae6ff5a17b049ed'},
            {'chapter': '2', 'url': 'http://bato.to/reader#7b3c06767fc2652c'},
            {'chapter': '3', 'url': 'http://bato.to/reader#f1ad5d28d81d4235'},
            {'chapter': '4', 'url': 'http://bato.to/reader#53b515ec0296fc09'}
        ]
        CHAPTERS4 = [
            {'chapter': '0', 'url': 'http://bato.to/reader#b989b624047f3e38'}
        ]
        FOLLOW1 = {'url': 'http://bato.to/comic/_/comics/femme-fatale-r468',
                   'alias': 'femme-fatale', 'name': 'Femme Fatale'}
        FOLLOW2 = {'url': 'http://bato.to/comic/_/comics/houkago-r9187',
                   'alias': 'houkago', 'name': 'Houkago'}
        FOLLOW3 = {'url': 'http://bato.to/comic/_/comics/dog-days-r6928',
                   'alias': 'dog-days', 'name': 'Houkago'}
        FOLLOW4 = {'url': 'http://bato.to/comic/_/comics/cat-gravity-r11269',
                   'alias': 'cat-gravity', 'name': 'Cat Gravity'}
        MESSAGES = [
            'Updating 3 series (1 skipped)',
            'femme-fatale 1  2  3  4  4.5  5  6  7  8  8.5  9  10  11  12',
        ]

        config.get().compact_new = True
        config.get().write()

        dates1 = [
            datetime.datetime.now() - datetime.timedelta(days=14),
            datetime.datetime.now() - datetime.timedelta(days=1)
        ]
        dates2 = [
            datetime.datetime.now() - datetime.timedelta(days=7)
        ]

        series = self.create_mock_series(**FOLLOW1)
        series.follow()
        series = self.create_mock_series(**FOLLOW2)
        for chapter in CHAPTERS2:
            chapter = self.create_mock_chapter(**chapter)
            series.chapters.append(chapter)
        series.follow()
        series = self.create_mock_series(**FOLLOW3)
        for chapter in CHAPTERS3:
            chapter = self.create_mock_chapter(**chapter)
            series.chapters.append(chapter)
        series.follow()
        series = self.create_mock_series(**FOLLOW4)
        for chapter in CHAPTERS4:
            chapter = self.create_mock_chapter(**chapter)
            series.chapters.append(chapter)
        series.follow()

        chapters = self.db.session.query(self.db.Chapter).all()
        for chapter in chapters:
            chapter.downloaded = 1
        self.db.session.commit()
        chapters = (self.db.session.query(self.db.Chapter)
                                   .filter_by(series_id=2)
                                   .all())
        for i, chapter in enumerate(chapters):
            chapter.added_on = dates1[i]
        self.db.session.commit()
        chapters = (self.db.session.query(self.db.Chapter)
                                   .filter_by(series_id=4)
                                   .all())
        for i, chapter in enumerate(chapters):
            chapter.added_on = dates2[i]
        self.db.session.commit()

        result = self.invoke('update', '--fast')
        chapters = self.db.session.query(self.db.Chapter).all()
        self.assertEqual(result.exit_code, 0)
        for message in MESSAGES:
            self.assertIn(message, result.output)

    def test_update_invalid_login(self):
        FOLLOW = {'url': 'http://bato.to/comic/_/comics/femme-fatale-r468',
                  'alias': 'femme-fatale', 'name': 'Femme Fatale'}
        MESSAGE = 'Unable to update femme-fatale (Batoto login error)'

        series = self.create_mock_series(**FOLLOW)
        series.follow()

        config.get().batoto.cookie = None
        config.get().batoto.member_id = None
        config.get().batoto.pass_hash = None
        config.get().batoto.password = 'Notvalid'
        config.get().batoto.username = 'Notvalid'
        config.get().write()

        result = self.invoke('update')
        self.assertEqual(result.exit_code, 0)
        self.assertIn(MESSAGE, result.output)
