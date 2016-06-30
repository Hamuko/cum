from bs4 import BeautifulSoup
from cum import config, exceptions
from urllib.parse import urljoin
import cumtest
import os
import re
import requests
import tempfile
import unittest
import zipfile


class TestBatoto(cumtest.CumTest):
    BATOTO_URL = 'http://bato.to/'

    def setUp(self):
        super().setUp()
        global batoto
        from cum.scrapers import batoto

    def tearDown(self):
        self.directory.cleanup()

    def get_five_latest_releases(self):
        r = requests.get(self.BATOTO_URL)
        soup = BeautifulSoup(r.text, config.get().html_parser)
        english_chapters = (soup.find('table', class_='chapters_list')
                                .find_all('tr', class_='lang_English'))
        links = []
        for chapter in english_chapters:
            links += [urljoin(self.BATOTO_URL, x.get('href')) for x in
                      chapter.find_all(href=re.compile(r'/reader#.*'))]
        return links[:5]

    def series_information_tester(self, data):
        series = batoto.BatotoSeries(data['url'])
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

    @cumtest.skipIfNoBatotoLogin
    def test_chapter_download_latest(self):
        latest_releases = self.get_five_latest_releases()
        for release in latest_releases:
            try:
                chapter = batoto.BatotoChapter.from_url(release)
            except exceptions.ScrapingError:
                continue
            else:
                chapter.get(use_db=False)

    @cumtest.skipIfNoBatotoLogin
    def test_chapter_filename_decimal(self):
        URL = 'http://bato.to/reader#ecd20142e8159ad0'
        chapter = batoto.BatotoChapter.from_url(URL)
        path = os.path.join(
            self.directory.name, 'Grape Pine',
            'Grape Pine - c005 x2 [Angelic Miracle Scanlations].zip'
        )
        self.assertEqual(chapter.chapter, '5.2')
        self.assertEqual(chapter.filename, path)

    @cumtest.skipIfNoBatotoLogin
    def test_chapter_filename_version2(self):
        URL = 'http://bato.to/reader#619ea101f703ecb2'
        chapter = batoto.BatotoChapter.from_url(URL)
        path = os.path.join(
            self.directory.name, 'Hitorimi Haduki-san to.',
            'Hitorimi Haduki-san to. - c005 [Ciel Scans].zip'
        )
        self.assertEqual(chapter.chapter, '5v2')
        self.assertEqual(chapter.filename, path)

    @cumtest.skipIfNoBatotoLogin
    def test_chapter_information_bakuon(self):
        URL = 'http://bato.to/reader#eb862784d9eff2be'
        chapter = batoto.BatotoChapter.from_url(URL)
        self.assertEqual(chapter.alias, 'bakuon')
        self.assertTrue(chapter.available())
        self.assertEqual(chapter.batoto_hash, 'eb862784d9eff2be')
        self.assertEqual(chapter.chapter, '01')
        self.assertEqual(chapter.groups, ['Low Gear'])
        self.assertEqual(chapter.name, 'Bakuon!!')
        self.assertEqual(chapter.title, 'The Uphill Road!!')
        path = os.path.join(self.directory.name,
                            'Bakuon',
                            'Bakuon - c001 [Low Gear].zip')
        self.assertEqual(chapter.filename, path)
        chapter.download()
        self.assertTrue(os.path.isfile(path))
        with zipfile.ZipFile(path) as chapter_zip:
            files = chapter_zip.infolist()
            self.assertEqual(len(files), 37)

    @cumtest.skipIfNoBatotoLogin
    def test_chapter_information_rotte_no_omocha(self):
        URL = 'http://bato.to/reader#d647e1267a7c2c54'
        chapter = batoto.BatotoChapter.from_url(URL)
        self.assertEqual(chapter.alias, 'rotte-no-omocha')
        self.assertEqual(chapter.batoto_hash, 'd647e1267a7c2c54')
        self.assertEqual(chapter.chapter, '1')
        self.assertEqual(chapter.groups, ['Facepalm Scans'])
        self.assertEqual(chapter.name, 'Rotte no Omocha!')
        self.assertEqual(chapter.title,
                         '"A Candidate for the Princess\'s Harem!?"')
        path = os.path.join(
            self.directory.name, 'Rotte no Omocha',
            'Rotte no Omocha - c001 [Facepalm Scans].zip'
        )
        self.assertEqual(chapter.filename, path)
        chapter.download()
        self.assertTrue(os.path.isfile(path))
        with zipfile.ZipFile(path) as chapter_zip:
            files = chapter_zip.infolist()
            self.assertEqual(len(files), 38)

    @cumtest.skipIfNoBatotoLogin
    def test_chapter_information_tomochan(self):
        URL = 'http://bato.to/reader#cf03b01bd9e90ba8'
        config.get().cbz = True
        chapter = batoto.BatotoChapter.from_url(URL)
        self.assertEqual(chapter.alias, 'tomo-chan-wa-onna-no-ko')
        self.assertTrue(chapter.batoto_hash, 'cf03b01bd9e90ba8')
        self.assertEqual(chapter.chapter, '1-10')
        self.assertEqual(chapter.groups, ['M@STERSCANZ'])
        self.assertEqual(chapter.name, 'Tomo-chan wa Onna no ko!')
        self.assertIs(chapter.title, None)
        path = os.path.join(
            self.directory.name, 'Tomo-chan wa Onna no ko',
            'Tomo-chan wa Onna no ko - c001-010 [MSTERSCANZ].cbz'
        )
        self.assertEqual(chapter.filename, path)
        chapter.download()
        self.assertTrue(os.path.isfile(path))
        with zipfile.ZipFile(path) as chapter_zip:
            files = chapter_zip.infolist()
            self.assertEqual(len(files), 10)

    @cumtest.skipIfNoBatotoLogin
    def test_chapter_unavailable_deleted(self):
        URL = 'http://bato.to/reader#ba173e587bdc9325'
        chapter = batoto.BatotoChapter(url=URL)
        self.assertFalse(chapter.available())

    @cumtest.skipIfNoBatotoLogin
    def test_chapter_unavailable_old_url(self):
        URL = 'http://bato.to/read/_/203799/shokugeki-no-soma_ch46_by_casanova'
        chapter = batoto.BatotoChapter(url=URL)
        self.assertFalse(chapter.available())

    @cumtest.skipIfNoBatotoLogin
    def test_outdated_session(self):
        URL = 'http://bato.to/comic/_/comics/femme-fatale-r468'
        config.get().batoto.cookie = '0da7ed'
        config.get().batoto.member_id = '0da7ed'
        config.get().batoto.pass_hash = '0da7ed'
        config.get().write()
        series = batoto.BatotoSeries(url=URL)

    def test_outdated_session_max_retries(self):
        URL = 'http://bato.to/comic/_/comics/femme-fatale-r468'
        config.get().batoto._login_attempts = 1
        config.get().batoto.cookie = '0da7ed'
        config.get().batoto.member_id = '0da7ed'
        config.get().batoto.pass_hash = '0da7ed'
        config.get().write()
        with self.assertRaises(exceptions.LoginError):
            series = batoto.BatotoSeries(url=URL)

    def test_series_invalid_login(self):
        URL = 'https://bato.to/comic/_/comics/stretch-r11259'
        config.get().batoto.password = '12345'
        config.get().batoto.username = 'KoalaBeer'
        with self.assertRaises(exceptions.LoginError):
            series = batoto.BatotoSeries(url=URL)

    def test_series_invalid_login_2(self):
        URL = 'https://bato.to/comic/_/comics/stretch-r11259'
        config.get().batoto.password = '12345'
        config.get().batoto.username = 'KoalaBeer'
        config.get().batoto.member_id = 'Invalid'
        config.get().batoto.pass_hash = 'Invalid'
        config.get().batoto.cookie = 'Invalid'
        with self.assertRaises(exceptions.LoginError):
            series = batoto.BatotoSeries(url=URL)

    @cumtest.skipIfNoBatotoLogin
    def test_series_molester_man(self):
        data = {'alias': 'molester-man',
                'chapters': ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10',
                             '11', '12', '13', '14', '14.5', '15', '16', '17',
                             '18', '19', '20', '21', '21.5'],
                'groups': ['Boon Scanlation'],
                'name': 'Molester Man',
                'url': 'http://bato.to/comic/_/comics/molester-man-r7471'}
        self.series_information_tester(data)

    @cumtest.skipIfNoBatotoLogin
    def test_series_prunus_girl(self):
        data = {'alias': 'prunus-girl',
                'chapters': ['1', '2', '3', '4', '5', '6', '6.5', '7', '8',
                             '9', '10', '11', '11.5', '12', '13', '14', '15',
                             '16', '16.5', '17', '18', '19', '20', '21', '22',
                             '23', '24', '25', '26', '27', '28', '29', '30',
                             '31', '32', '32.5', '33', '34', '35', '36', '37',
                             '38', '39', '40', '41', '42', 'Epilogue'],
                'groups': ['No Group', 'Maigo', 'WOWScans!'],
                'name': 'Prunus Girl',
                'url': 'http://bato.to/comic/_/comics/prunus-girl-r18'}
        self.series_information_tester(data)

if __name__ == '__main__':
    unittest.main()
