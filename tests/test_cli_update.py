from cum import config
from unittest import mock
import cumtest
import datetime


class TestCLIUpdate(cumtest.CumCLITest):
    def test_update(self):
        FOLLOWS = [
            {'url': 'https://dynasty-scans.com/series/himegoto_1',
             'alias': 'himegoto', 'name': 'Himegoto+'},
            {'url': ('https://manga.madokami.al/Manga/N/NU/NUDE/Nude%20na%20Shisen'),
             'alias': 'nude-na-shisen',
             'name': 'Nude na Shisen'}
        ]
        MESSAGES = [
            'Updating 2 series',
            'himegoto 1  2  3  4  5  6  7'
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
        self.assertEqual(len(chapters), 7)

    def test_update_fast(self):
        CHAPTERS2 = [
            {'chapter': '1',
             'url': ('https://kobato.hologfx.com/reader/read/'
                     'hitoribocchi_no_oo_seikatsu/en/1/1/')},
            {'chapter': '2',
             'url': ('https://kobato.hologfx.com/reader/read/'
                     'hitoribocchi_no_oo_seikatsu/en/1/2/')},
        ]
        CHAPTERS3 = [
            {'chapter': '1',
             'url': 'https://dynasty-scans.com/chapters/i_girl_ch01'},
            {'chapter': '2',
             'url': 'https://dynasty-scans.com/chapters/i_girl_ch02'}
        ]
        CHAPTERS4 = [
            {'chapter': '3',
             'url': ('https://manga.madokami.al/Manga/N/NU/NUSA/Nusantara%20'
                     'Droid%20War/Nusantara%20Droid%20War%20Ch.003%20And%20The'
                     '%20Winner%20Is....%20%5BKissManga%5D.zip')}
        ]
        FOLLOW1 = {'url': 'https://dynasty-scans.com/series/himegoto_1',
                   'alias': 'himegoto', 'name': 'Himegoto+'}
        FOLLOW2 = {'url': ('https://kobato.hologfx.com/reader/series/'
                           'hitoribocchi_no_oo_seikatsu/'),
                   'alias': 'hitoribocchi-no-oo-seikatsu',
                   'name': 'Hitoribocchi no OO Seikatsu'}
        FOLLOW3 = {'url': 'https://dynasty-scans.com/series/i_girl',
                   'alias': 'i-girl', 'name': 'I Girl'}
        FOLLOW4 = {'url': ('https://manga.madokami.al/Manga/N/NU/NUDE/Nude%20na%20Shisen'),
                   'alias': 'nude-na-shisen',
                   'name': 'Nude na Shisen'}
        MESSAGES = [
            'Updating 3 series (1 skipped)',
            'himegoto 1  2  3  4  5  6  7',
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
