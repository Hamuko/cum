from cum import config
from unittest import mock
import cumtest


class TestCLINew(cumtest.CumCLITest):
    CHAPTERS = [
        {'url': 'https://dynasty-scans.com/chapters/nijipuri_ch01',
         'chapter': '1'},
        {'url': 'https://dynasty-scans.com/chapters/nijipuri_ch02',
         'chapter': '2'},
        {'url': 'https://dynasty-scans.com/chapters/nijipuri_ch03',
         'chapter': '3'},
        {'url': 'https://dynasty-scans.com/chapters/nijipuri_ch04',
         'chapter': '4'},
        {'url': 'https://dynasty-scans.com/chapters/nijipuri_ch05',
         'chapter': '5'},
        {'url': 'https://dynasty-scans.com/chapters/nijipuri_ch06',
         'chapter': '6'},
    ]
    FOLLOW = {'url': 'https://dynasty-scans.com/series/nijipuri',
              'name': 'Nijipuri', 'alias': 'nijipuri'}

    def create_test_data(self):
        series = self.create_mock_series(**self.FOLLOW)
        for chapter_info in self.CHAPTERS:
            chapter = self.create_mock_chapter(**chapter_info)
            series.chapters.append(chapter)
        series.follow()

    def test_new(self):
        MESSAGES = ['nijipuri', '1  2  3  4  5  6']

        self.create_test_data()

        result = self.invoke('new')
        self.assertEqual(result.exit_code, 0)
        for message in MESSAGES:
            self.assertIn(message, result.output)

    def test_new_empty(self):
        result = self.invoke('new')
        self.assertEqual(result.exit_code, 0)
        self.assertFalse(result.output)

    def test_new_compact(self):
        MESSAGE = 'nijipuri 1  2  3  4  5  6'

        config.get().compact_new = True
        config.get().write()
        self.create_test_data()

        result = self.invoke('new')
        self.assertEqual(result.exit_code, 0)
        self.assertIn(MESSAGE, result.output)

    def test_new_compact_empty(self):
        config.get().compact_new = True
        config.get().write()

        result = self.invoke('new')
        self.assertEqual(result.exit_code, 0)
        self.assertFalse(result.output)

    def test_new_broken_database(self):
        MESSAGES = [
            'groups table is missing from database',
            'chapters.title column has inappropriate datatype INTEGER '
            '(should be VARCHAR)',
            'chapters.title is not nullable',
            'series.directory column is missing from database',
            'series.alias is nullable',
            'Database has failed sanity check'
        ]

        self.copy_broken_database()

        result = self.invoke('new')
        self.assertEqual(result.exit_code, 1)
        for message in MESSAGES:
            self.assertIn(message, result.output)

    def test_new_broken_madokami_domain(self):
        SERIES = {'url': 'https://manga.madokami.com/Manga/O/OJ/OJOJ/Ojojojo',
                  'name': 'Ojojojo', 'alias': 'ojojojo'}
        CHAPTER = {'url': 'https://manga.madokami.com/Manga/O/OJ/OJOJ/Ojojojo/'
                          'Ojojojo%20c001.rar', 'chapter': '1'}
        MESSAGES = ['series has entries with incorrect domain '
                    '(manga.madokami.com -> manga.madokami.al)',
                    'chapters has entries with incorrect domain '
                    '(manga.madokami.com -> manga.madokami.al)',
                    'Database has failed sanity check; run `cum repair-db` '
                    'to repair database']
        SERIES_URL = 'https://manga.madokami.al/Manga/O/OJ/OJOJ/Ojojojo'
        CHAPTER_URL = ('https://manga.madokami.al/Manga/O/OJ/OJOJ/Ojojojo/'
                       'Ojojojo%20c001.rar')

        series = self.create_mock_series(**SERIES)
        chapter = self.create_mock_chapter(**CHAPTER)
        series.chapters.append(chapter)
        series.follow()

        result = self.invoke('new')
        self.assertEqual(result.exit_code, 1)
        for message in MESSAGES:
            self.assertIn(message, result.output)

        result = self.invoke('repair-db')
        self.assertEqual(result.exit_code, 0)

        series = self.db.session.query(self.db.Series).first()
        chapter = self.db.session.query(self.db.Chapter).first()
        self.assertEqual(series.url, SERIES_URL)
        self.assertEqual(chapter.url, CHAPTER_URL)
