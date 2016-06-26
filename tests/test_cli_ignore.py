from unittest import mock
import cumtest


class TestCLIIgnore(cumtest.CumCLITest):
    def test_ignore(self):
        CHAPTER = {'url': 'http://bato.to/reader#edd5272771db4e0d',
                   'chapter': '0'}
        FOLLOW = {'url': 'http://bato.to/comic/_/eien-no-mae-r8817',
                  'alias': 'eien-no-mae', 'name': 'Eien no Mae'}
        MESSAGE = 'Ignored chapter 0 for Eien no Mae'

        series = self.create_mock_series(**FOLLOW)
        chapter = self.create_mock_chapter(**CHAPTER)
        series.chapters.append(chapter)
        series.follow()

        result = self.invoke('ignore', 'eien-no-mae', '0')
        chapter = self.db.session.query(self.db.Chapter).first()
        self.assertEqual(result.exit_code, 0)
        self.assertIn(MESSAGE, result.output)
        self.assertEqual(chapter.downloaded, -1)

    def test_ignore_all(self):
        CHAPTERS = [
            {'url': 'http://bato.to/reader#b8f0d2e43d2ed424', 'chapter': '1'},
            {'url': 'http://bato.to/reader#a7abba3b7dfbd5e3', 'chapter': '2'},
            {'url': 'http://bato.to/reader#ac164a18fed77408', 'chapter': '3'},
            {'url': 'http://bato.to/reader#d28de8d8ee689ec1', 'chapter': '4'},
            {'url': 'http://bato.to/reader#a933477ef8650f39', 'chapter': '5'}
        ]
        FOLLOW = {'url': 'http://bato.to/comic/_/comics/fetish-r1133',
                  'alias': 'fetish', 'name': 'Fetish'}
        MESSAGE = 'Ignored 5 chapters for Fetish'

        series = self.create_mock_series(**FOLLOW)
        for chapter in CHAPTERS:
            chapter = self.create_mock_chapter(**chapter)
            series.chapters.append(chapter)
        series.follow()

        result = self.invoke('ignore', 'fetish', 'all', input='y')
        chapters = self.db.session.query(self.db.Chapter).all()
        self.assertEqual(result.exit_code, 0)
        self.assertIn(MESSAGE, result.output)
        for chapter in chapters:
            self.assertEqual(chapter.downloaded, -1)
