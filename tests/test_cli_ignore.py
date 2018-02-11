from unittest import mock
import cumtest


class TestCLIIgnore(cumtest.CumCLITest):
    def setUp(self):
        super().setUp()
        CHAPTERS = [
            {'url': ('https://manga.madokami.al/Manga/Z/ZO/ZONE/Zone-00/Zone-'
                     '00%20v01%20c01.zip'),
             'chapter': '1'},
            {'url': ('https://manga.madokami.al/Manga/Z/ZO/ZONE/Zone-00/Zone-'
                     '00%20v01%20c02.rar'),
             'chapter': '2'},
            {'url': ('https://manga.madokami.al/Manga/Z/ZO/ZONE/Zone-00/Zone-'
                     '00%20v01%20c03.zip'),
             'chapter': '3'},
            {'url': ('https://manga.madokami.al/Manga/Z/ZO/ZONE/Zone-00/Zone-'
                     '00%20v01%20c04.zip'),
             'chapter': '4'},
        ]
        FOLLOW = {
            'url': ('https://manga.madokami.al/Manga/Z/ZO/ZONE/Zone-00/Zone-'
                    '00%20v01%20c01.zip'),
            'alias': 'zone-00',
            'name': 'Zone-00'
        }
        series = self.create_mock_series(**FOLLOW)
        for chapter in CHAPTERS:
            chapter = self.create_mock_chapter(**chapter)
            series.chapters.append(chapter)
        series.follow()

    def test_ignore(self):
        MESSAGE = 'Ignored chapter 3 for Zone-00'

        result = self.invoke('ignore', 'zone-00', '3')
        chapter = self.db.session.query(self.db.Chapter)\
                                 .filter_by(chapter=3).one()
        self.assertEqual(result.exit_code, 0)
        self.assertIn(MESSAGE, result.output)
        self.assertEqual(chapter.downloaded, -1)

    def test_ignore_all(self):
        MESSAGE = 'Ignored 4 chapters for Zone-00'

        result = self.invoke('ignore', 'zone-00', 'all', input='y')
        chapters = self.db.session.query(self.db.Chapter).all()
        self.assertEqual(result.exit_code, 0)
        self.assertIn(MESSAGE, result.output)
        for chapter in chapters:
            self.assertEqual(chapter.downloaded, -1)
