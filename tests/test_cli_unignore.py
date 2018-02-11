from unittest import mock
import cumtest


class TestCLIUnignore(cumtest.CumCLITest):
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

        chapters = self.db.session.query(self.db.Chapter).all()
        for chapter in chapters:
            chapter.downloaded = -1
        self.db.session.commit()

    def test_unignore(self):
        MESSAGE = 'Unignored chapter 2 for Zone-00'

        result = self.invoke('unignore', 'zone-00', '2')
        chapter = self.db.session.query(self.db.Chapter)\
                                 .filter_by(chapter=2).one()
        self.assertEqual(result.exit_code, 0)
        self.assertIn(MESSAGE, result.output)
        self.assertEqual(chapter.downloaded, 0)

    def test_unignore_all(self):
        MESSAGE = 'Unignored 4 chapters for Zone-00'

        result = self.invoke('unignore', 'zone-00', 'all', input='y')
        chapters = self.db.session.query(self.db.Chapter).all()
        self.assertEqual(result.exit_code, 0)
        self.assertIn(MESSAGE, result.output)
        for chapter in chapters:
            self.assertEqual(chapter.downloaded, 0)
