from cum import config, exceptions
import cumtest
import os
import unittest


class TestMadokami(cumtest.CumTest):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        NO_MADOKAMI_LOGIN = self.no_madokami_login

    def setUp(self):
        super().setUp()
        global madokami
        from cum.scrapers import madokami

    def series_information_tester(self, data):
        series = madokami.MadokamiSeries(data['url'])
        self.assertEqual(series.name, data['name'])
        self.assertEqual(series.alias, data['alias'])
        self.assertEqual(series.url, data['url'])
        self.assertIs(series.directory, None)
        self.assertEqual(len(series.chapters), len(data['chapters']))
        for chapter in series.chapters:
            self.assertEqual(chapter.name, data['name'])
            self.assertEqual(chapter.alias, data['alias'])
            self.assertIn(chapter.chapter, data['chapters'])
            data['chapters'].remove(chapter.chapter)
            for group in chapter.groups:
                self.assertIn(group, data['groups'])
            self.assertIs(chapter.directory, None)
        self.assertEqual(len(data['chapters']), 0)

    @cumtest.skipIfNoMadokamiLogin
    def test_chapter_filename_no_group(self):
        URL = ('https://manga.madokami.al/Manga/_/__/__DA/7-Daime%20no%20'
               'Tomari%21/7-Daime%20no%20Tomari%21%20v01%20c01.zip')
        chapter = madokami.MadokamiChapter.from_url(URL)
        self.assertEqual(chapter.chapter, '01')
        self.assertEqual(len(chapter.groups), 0)
        path = os.path.join(
            self.directory.name, '7-Daime no Tomari',
            '7-Daime no Tomari - c001 [Unknown].zip'
        )
        self.assertEqual(chapter.filename, path)

    def test_chapter_invalid_login(self):
        URL = ('https://manga.madokami.al/Manga/Oneshots/100%20Dollar%20wa%20'
               'Yasu%20Sugiru/100%24%20is%20Too%20Cheap%20%5BYAMAMOTO%20Kazune'
               '%5D%20-%20000%20%5BOneshot%5D%20%5BPeebs%5D.zip')
        config.get().madokami.password = '12345'
        config.get().madokami.username = 'Koala'
        with self.assertRaises(exceptions.LoginError):
            madokami.MadokamiChapter.from_url(URL)

    @cumtest.skipIfNoMadokamiLogin
    def test_chapter_100_dollar_too_cheap(self):
        URL = ('https://manga.madokami.al/Manga/Oneshots/100%20Dollar%20wa%20'
               'Yasu%20Sugiru/100%24%20is%20Too%20Cheap%20%5BYAMAMOTO%20Kazune'
               '%5D%20-%20000%20%5BOneshot%5D%20%5BPeebs%5D.zip')
        NAME = '100 Dollar wa Yasu Sugiru'
        chapter = madokami.MadokamiChapter.from_url(URL)
        self.assertEqual(chapter.alias, '100-dollar-wa-yasu-sugiru')
        self.assertTrue(chapter.available())
        self.assertEqual(chapter.chapter, '000 [Oneshot]')
        self.assertIs(chapter.directory, None)
        self.assertEqual(chapter.groups, ['Peebs'])
        self.assertEqual(chapter.name, NAME)
        self.assertEqual(chapter.url, URL)
        path = os.path.join(
            self.directory.name, NAME,
            '100 Dollar wa Yasu Sugiru - c000 [000 [Oneshot]] [Peebs].zip'
        )
        self.assertEqual(chapter.filename, path)
        chapter.download()
        self.assertTrue(os.path.isfile(path))

    @cumtest.skipIfNoMadokamiLogin
    def test_name_fallback(self):
        NAME = '!Koukaku no Pandora - Ghost Urn [Seven Seas]'
        URL = ('https://manga.madokami.al/Manga/K/KO/KOUK/Koukaku%20no%20'
               'Pandora%20-%20Ghost%20Urn/%21Koukaku%20no%20Pandora%20-%20'
               'Ghost%20Urn%20%5BSeven%20Seas%5D')
        series = madokami.MadokamiSeries(URL)
        self.assertEqual(series.name, NAME)

    @cumtest.skipIfNoMadokamiLogin
    def test_series_kami_nomi(self):
        data = {
            'alias': 'kami-nomi-zo-shiru-sekai',
            'chapters': ['Koishite!', '001-006', '007-016', '017-026',
                         '027-036', '037-046', '047-056', '057-066', '067-076',
                         '077-086', '087-096', '097-106', '107-116', '117-126',
                         '127-136', '137-146', '147-156', '157-167', '168-178',
                         '179-189', '190-200', '201-211', '212-222', '223-233',
                         '234-244', '245-256', '257-268'],
            'groups': [None],
            'name': 'Kami nomi zo Shiru Sekai',
            'url': 'https://manga.madokami.al/Manga/K/KA/KAMI/Kami%20nomi%20'
                   'zo%20Shiru%20Sekai'
        }
        self.series_information_tester(data)

    @cumtest.skipIfNoMadokamiLogin
    def test_series_medaka_box(self):
        data = {
            'alias': 'medaka-box',
            'chapters': [
                '000 (OShot) [mag]',
                '001-007',
                '001-007',
                '008-016',
                '017-025',
                '026-034',
                '035-043',
                '044-052',
                '053-061',
                '062-070',
                '071-079',
                '080-088',
                '089-097',
                '098-106',
                '107-115',
                '116-124',
                '125-131',
                '132-140',
                '141-149',
                '150-158',
                '159-167',
                '168-176',
                '177-185',
                '186-192',
            ],
            'groups': ['CXCScans', 'mix] [Various',
                       'mix] [CXCScans & IMS', 'mix] [CXCScans'],
            'name': 'Medaka Box',
            'url': 'https://manga.madokami.al/Manga/M/ME/MEDA/Medaka%20Box'
        }
        self.series_information_tester(data)
