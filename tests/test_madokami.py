from cum import config, exceptions
import os
import tempfile
import unittest


class TestMadokami(unittest.TestCase):
    BATOTO_URL = 'http://bato.to/'

    def setUp(self):
        global madokami
        self.directory = tempfile.TemporaryDirectory()
        config.initialize(directory=self.directory.name)
        config.get().madokami.password = os.environ['MADOKAMI_PASSWORD']
        config.get().madokami.username = os.environ['MADOKAMI_USERNAME']
        config.get().download_directory = self.directory.name
        from cum.scrapers import madokami

    def tearDown(self):
        self.directory.cleanup()

    def series_information_tester(self, data):
        series = madokami.MadokamiSeries(data['url'])
        assert series.name == data['name']
        assert series.alias == data['alias']
        assert series.url == data['url']
        assert series.directory is None
        assert len(series.chapters) == len(data['chapters'])
        for chapter in series.chapters:
            assert chapter.name == data['name']
            assert chapter.alias == data['alias']
            assert chapter.chapter in data['chapters']
            data['chapters'].remove(chapter.chapter)
            for group in chapter.groups:
                assert group in data['groups']
            assert chapter.directory is None
        assert len(data['chapters']) == 0

    def test_chapter_filename_no_group(self):
        URL = ('https://manga.madokami.com/Manga/_/__/__DA/7-Daime%20no%20'
               'Tomari%21/7-Daime%20no%20Tomari%21%20v01%20c01.zip')
        chapter = madokami.MadokamiChapter.from_url(URL)
        assert chapter.chapter == '01'
        assert len(chapter.groups) == 0
        path = os.path.join(
            self.directory.name, '7-Daime no Tomari',
            '7-Daime no Tomari - c001 [Unknown].zip'
        )
        assert chapter.filename == path

    def test_chapter_invalid_login(self):
        config.get().madokami.password = '12345'
        config.get().madokami.username = 'Koala'
        with self.assertRaises(exceptions.LoginError):
            self.test_chapter_100_dollar_too_cheap()

    def test_chapter_100_dollar_too_cheap(self):
        URL = ('https://manga.madokami.com/Manga/Oneshots/100%20Dollar%20wa%20'
               'Yasu%20Sugiru/100%24%20is%20Too%20Cheap%20%5BYAMAMOTO%20Kazune'
               '%5D%20-%20000%20%5BOneshot%5D%20%5BPeebs%5D.zip')
        NAME = '100 Dollar wa Yasu Sugiru'
        chapter = madokami.MadokamiChapter.from_url(URL)
        assert chapter.alias == '100-dollar-wa-yasu-sugiru'
        assert chapter.available() is True
        assert chapter.chapter == '000 [Oneshot]'
        assert chapter.directory is None
        assert chapter.groups == ['Peebs']
        assert chapter.name == NAME
        assert chapter.url == URL
        path = os.path.join(
            self.directory.name, NAME,
            '100 Dollar wa Yasu Sugiru - c000 [000 [Oneshot]] [Peebs].zip'
        )
        assert chapter.filename == path
        chapter.download()
        assert os.path.isfile(path) is True

    def test_series_kami_nomi(self):
        data = {
            'alias': 'kami-nomi-zo-shiru-sekai',
            'chapters': ['Koishite!', '01-06', '07-16', '17-26', '27-36',
                         '37-46', '47-56', '57-66', '67-76', '77-86', '87-96',
                         '97-106', '107-116', '117-126', '127-136', '137-146',
                         '147-156', '157-167', '168-178', '179-189', '190-200',
                         '201-211', '212-222', '223-233', '234-244', '245-256',
                         '257-268'],
            'groups': [None],
            'name': 'Kami nomi zo Shiru Sekai',
            'url': 'https://manga.madokami.com/Manga/K/KA/KAMI/Kami%20nomi%20'
                   'zo%20Shiru%20Sekai'
        }
        self.series_information_tester(data)

    def test_series_medaka_box(self):
        data = {
            'alias': 'medaka-box',
            'chapters': ['001-007', '008-016', '017-025', '026-034', '035-043',
                         '044-052', '053-061', '062-070', '071-079', '080-088',
                         '089-097', '098-106', '107-115', '116-124', '125-131',
                         '132-140', '141-149', '150-158', '159-167', '168-176',
                         '177-185', '186-192'],
            'groups': ['CXC', 'CXC+anon', 'CXC+ims',
                       'CXC-ims', 'ims+DBR', 'Sammy+ims+DBR'],
            'name': 'Medaka Box',
            'url': 'https://manga.madokami.com/Manga/M/ME/MEDA/Medaka%20Box'
        }
        self.series_information_tester(data)

if __name__ == '__main__':
    unittest.main()
