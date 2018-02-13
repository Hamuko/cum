from unittest import mock
import cumtest
import datetime
import time


class TestCLILatest(cumtest.CumCLITest):
    SERIES_KWARGS = {'url': ('https://manga.madokami.al/Manga/K/KA/KANG/'
                             'Kangoku%20Gakuen'),
                     'alias': 'kangoku-gakuen', 'name': 'Kangoku Gakuen'}
    CHAPTER_KWARGS = {
        'chapter': '0',
        'url': ('https://manga.madokami.al/Manga/K/KA/KANG/Kangoku%20Gakuen/'
                'Kangoku%20Gakuen%20%28Prison%20School%29%20-%20c001-008%20%28'
                'v01%29%20%5BEMS%5D.zip')
    }

    def setUp(self):
        super().setUp()
        series = self.create_mock_series(**self.SERIES_KWARGS)
        chapter = self.create_mock_chapter(**self.CHAPTER_KWARGS)
        series.chapters.append(chapter)
        series.follow()

    def test_latest(self):
        MESSAGE = 'kangoku-gakuen   2013-12-11 10:09'

        chapter = self.db.session.query(self.db.Chapter).first()
        chapter.added_on = datetime.datetime(2013, 12, 11, hour=10, minute=9)
        self.db.session.commit()

        result = self.invoke('latest')
        self.assertEqual(result.exit_code, 0)
        self.assertIn(MESSAGE, result.output)

    def test_latest_alias(self):
        FOLLOW = {'url': 'https://manga.madokami.al/Manga/C/CE/CERB/Cerberus',
                  'alias': 'cerberus', 'name': 'Cerberus'}
        CHAPTER = {
            'chapter': '1',
            'url': ('https://manga.madokami.al/Manga/C/CE/CERB/Cerberus/'
                    'Cerberus%20v01%20c01-06.rar')
        }
        MESSAGE = 'kangoku-gakuen   2013-12-11 10:09\n'

        series = self.create_mock_series(**FOLLOW)
        chapter = self.create_mock_chapter(**CHAPTER)
        series.chapters.append(chapter)
        series.follow()

        chapter = self.db.session.query(self.db.Chapter).first()
        chapter.added_on = datetime.datetime(2013, 12, 11, hour=10, minute=9)
        self.db.session.commit()

        result = self.invoke('latest', 'kangoku-gakuen')
        self.assertEqual(result.exit_code, 0)
        self.assertIn(MESSAGE, result.output)
        self.assertNotIn(FOLLOW['alias'], result.output)

    def test_latest_never(self):
        MESSAGE = 'kangoku-gakuen   never'

        chapter = self.db.session.query(self.db.Chapter).first()
        self.db.session.delete(chapter)
        self.db.session.commit()

        result = self.invoke('latest')
        self.assertEqual(result.exit_code, 0)
        self.assertIn(MESSAGE, result.output)

    def test_latest_relative_days(self):
        MESSAGE = 'kangoku-gakuen   14 days ago'

        chapter = self.db.session.query(self.db.Chapter).first()
        time = datetime.datetime.now() - datetime.timedelta(days=14)
        chapter.added_on = time
        self.db.session.commit()

        result = self.invoke('latest', '--relative')
        self.assertEqual(result.exit_code, 0)
        self.assertIn(MESSAGE, result.output)

    def test_latest_relative_hours(self):
        MESSAGE = 'kangoku-gakuen   3 hours ago'

        chapter = self.db.session.query(self.db.Chapter).first()
        time = datetime.datetime.now() - datetime.timedelta(hours=3)
        chapter.added_on = time
        self.db.session.commit()

        result = self.invoke('latest', '--relative')
        self.assertEqual(result.exit_code, 0)
        self.assertIn(MESSAGE, result.output)

    def test_latest_relative_minutes(self):
        MESSAGE = 'kangoku-gakuen   1 minute ago'

        chapter = self.db.session.query(self.db.Chapter).first()
        time = datetime.datetime.now() - datetime.timedelta(minutes=1)
        chapter.added_on = time
        self.db.session.commit()

        result = self.invoke('latest', '--relative')
        self.assertEqual(result.exit_code, 0)
        self.assertIn(MESSAGE, result.output)

    def test_latest_relative_months(self):
        MESSAGE = 'kangoku-gakuen   2 months ago'

        chapter = self.db.session.query(self.db.Chapter).first()
        time = datetime.datetime.now() - datetime.timedelta(days=69)
        chapter.added_on = time
        self.db.session.commit()

        result = self.invoke('latest', '--relative')
        self.assertEqual(result.exit_code, 0)
        self.assertIn(MESSAGE, result.output)

    def test_latest_relative_seconds(self):
        MESSAGES = ['kangoku-gakuen   ', 'seconds ago']

        result = self.invoke('latest', '--relative')
        self.assertEqual(result.exit_code, 0)
        for message in MESSAGES:
            self.assertIn(message, result.output)
