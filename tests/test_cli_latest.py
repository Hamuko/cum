from unittest import mock
import cumtest
import datetime
import time


class TestCLILatest(cumtest.CumCLITest):
    SERIES_KWARGS = {'url': 'http://bato.to/comic/_/comics/cat-gravity-r11269',
                     'alias': 'cat-gravity', 'name': 'Cat Gravity'}
    CHAPTER_KWARGS = {
        'chapter': '0',
        'url': 'http://bato.to/reader#b989b624047f3e38'
    }

    def setUp(self):
        super().setUp()
        series = self.create_mock_series(**self.SERIES_KWARGS)
        chapter = self.create_mock_chapter(**self.CHAPTER_KWARGS)
        series.chapters.append(chapter)
        series.follow()

    def test_latest(self):
        MESSAGE = 'cat-gravity   2013-12-11 10:09'

        chapter = self.db.session.query(self.db.Chapter).first()
        chapter.added_on = datetime.datetime(2013, 12, 11, hour=10, minute=9)
        self.db.session.commit()

        result = self.invoke('latest')
        self.assertEqual(result.exit_code, 0)
        self.assertIn(MESSAGE, result.output)

    def test_latest_alias(self):
        FOLLOW = {'url': 'http://bato.to/comic/_/comics/cerberus-r1588',
                  'alias': 'cerberus', 'name': 'Cerberus'}
        CHAPTER = {
            'chapter': '1',
            'url': 'http://bato.to/reader#e5711cadcf1e387e'
        }
        MESSAGE = 'cat-gravity   2013-12-11 10:09\n'

        series = self.create_mock_series(**FOLLOW)
        chapter = self.create_mock_chapter(**CHAPTER)
        series.chapters.append(chapter)
        series.follow()

        chapter = self.db.session.query(self.db.Chapter).first()
        chapter.added_on = datetime.datetime(2013, 12, 11, hour=10, minute=9)
        self.db.session.commit()

        result = self.invoke('latest', 'cat-gravity')
        self.assertEqual(result.exit_code, 0)
        self.assertIn(MESSAGE, result.output)
        self.assertNotIn(FOLLOW['alias'], result.output)

    def test_latest_never(self):
        MESSAGE = 'cat-gravity   never'

        chapter = self.db.session.query(self.db.Chapter).first()
        self.db.session.delete(chapter)
        self.db.session.commit()

        result = self.invoke('latest')
        self.assertEqual(result.exit_code, 0)
        self.assertIn(MESSAGE, result.output)

    def test_latest_relative_days(self):
        MESSAGE = 'cat-gravity   14 days ago'

        chapter = self.db.session.query(self.db.Chapter).first()
        time = datetime.datetime.now() - datetime.timedelta(days=14)
        chapter.added_on = time
        self.db.session.commit()

        result = self.invoke('latest', '--relative')
        self.assertEqual(result.exit_code, 0)
        self.assertIn(MESSAGE, result.output)

    def test_latest_relative_hours(self):
        MESSAGE = 'cat-gravity   3 hours ago'

        chapter = self.db.session.query(self.db.Chapter).first()
        time = datetime.datetime.now() - datetime.timedelta(hours=3)
        chapter.added_on = time
        self.db.session.commit()

        result = self.invoke('latest', '--relative')
        self.assertEqual(result.exit_code, 0)
        self.assertIn(MESSAGE, result.output)

    def test_latest_relative_minutes(self):
        MESSAGE = 'cat-gravity   1 minute ago'

        chapter = self.db.session.query(self.db.Chapter).first()
        time = datetime.datetime.now() - datetime.timedelta(minutes=1)
        chapter.added_on = time
        self.db.session.commit()

        result = self.invoke('latest', '--relative')
        self.assertEqual(result.exit_code, 0)
        self.assertIn(MESSAGE, result.output)

    def test_latest_relative_months(self):
        MESSAGE = 'cat-gravity   2 months ago'

        chapter = self.db.session.query(self.db.Chapter).first()
        time = datetime.datetime.now() - datetime.timedelta(days=69)
        chapter.added_on = time
        self.db.session.commit()

        result = self.invoke('latest', '--relative')
        self.assertEqual(result.exit_code, 0)
        self.assertIn(MESSAGE, result.output)

    def test_latest_relative_seconds(self):
        MESSAGES = ['cat-gravity   ', 'seconds ago']

        result = self.invoke('latest', '--relative')
        self.assertEqual(result.exit_code, 0)
        for message in MESSAGES:
            self.assertIn(message, result.output)
