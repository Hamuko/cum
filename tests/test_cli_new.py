from cum import config
from unittest import mock
import cumtest


class TestCLINew(cumtest.CumCLITest):
    CHAPTERS = [
        {'url': 'http://bato.to/reader#4a9eb84cb52b62f6', 'chapter': '1-4'},
        {'url': 'http://bato.to/reader#63f3517dd93f7168', 'chapter': '5-8'},
        {'url': 'http://bato.to/reader#9a7916fddd6cdbf7', 'chapter': '9-12'},
        {'url': 'http://bato.to/reader#c80a8e4a99753d33', 'chapter': '13-16'},
        {'url': 'http://bato.to/reader#1505b31c009f51aa', 'chapter': '17-20'},
    ]
    FOLLOW = {'url': 'http://bato.to/comic/_/comics/blood-r5840',
              'name': 'BLOOD+', 'alias': 'blood'}

    def create_test_data(self):
        series = self.create_mock_series(**self.FOLLOW)
        for chapter_info in self.CHAPTERS:
            chapter = self.create_mock_chapter(**chapter_info)
            series.chapters.append(chapter)
        series.follow()

    def test_new(self):
        MESSAGES = ['blood', '1-4  5-8  9-12  13-16  17-20']

        self.create_test_data()

        result = self.invoke('new')
        self.assertEqual(result.exit_code, 0)
        for message in MESSAGES:
            assert message in result.output

    def test_new_empty(self):
        result = self.invoke('new')
        self.assertEqual(result.exit_code, 0)
        self.assertFalse(result.output)

    def test_new_compact(self):
        MESSAGE = 'blood 1-4  5-8  9-12  13-16  17-20'

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
        MESSAGES = ['groups table is missing from database',
                    'chapters.title column has inappropriate datatype INTEGER '
                    '(should be VARCHAR)',
                    'series.directory column is missing from database',
                    'Database has failed sanity check; run `cum repair-db` to '
                    'repair database']

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
