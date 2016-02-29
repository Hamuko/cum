from urllib.parse import urljoin
from bs4 import BeautifulSoup
from cum import config, exceptions
import os
import requests
import tempfile
import unittest
import zipfile
import re


class TestBatoto(unittest.TestCase):
    BATOTO_URL = 'http://bato.to/'

    def setUp(self):
        global batoto
        self.directory = tempfile.TemporaryDirectory()
        config.initialize(directory=self.directory.name)
        config.get().batoto.password = os.environ['BATOTO_PASSWORD']
        config.get().batoto.username = os.environ['BATOTO_USERNAME']
        config.get().download_directory = self.directory.name
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

    def test_chapter_download_latest(self):
        latest_releases = self.get_five_latest_releases()
        for release in latest_releases:
            try:
                chapter = batoto.BatotoChapter.from_url(release)
            except exceptions.ScrapingError:
                continue
            else:
                chapter.get(use_db=False)

    def test_chapter_filename_decimal(self):
        URL = 'http://bato.to/reader#ecd20142e8159ad0'
        chapter = batoto.BatotoChapter.from_url(URL)
        path = os.path.join(
            self.directory.name, 'Grape Pine',
            'Grape Pine - c005 x2 [Angelic Miracle Scanlations].zip'
        )
        assert chapter.chapter == '5.2'
        assert chapter.filename == path

    def test_chapter_filename_version2(self):
        URL = 'http://bato.to/reader#619ea101f703ecb2'
        chapter = batoto.BatotoChapter.from_url(URL)
        path = os.path.join(
            self.directory.name, 'Hitorimi Haduki-san to.',
            'Hitorimi Haduki-san to. - c005 [Ciel Scans].zip'
        )
        assert chapter.chapter == '5v2'
        assert chapter.filename == path

    def test_chapter_information_bakuon(self):
        URL = 'http://bato.to/reader#eb862784d9eff2be'
        chapter = batoto.BatotoChapter.from_url(URL)
        assert chapter.alias == 'bakuon'
        assert chapter.available() is True
        assert chapter.batoto_hash == 'eb862784d9eff2be'
        assert chapter.chapter == '01'
        assert chapter.groups == ['Low Gear']
        assert chapter.name == 'Bakuon!!'
        assert chapter.title == 'The Uphill Road!!'
        path = os.path.join(self.directory.name,
                            'Bakuon',
                            'Bakuon - c001 [Low Gear].zip')
        assert chapter.filename == path
        chapter.download()
        assert os.path.isfile(path) is True
        with zipfile.ZipFile(path) as chapter_zip:
            files = chapter_zip.infolist()
            assert len(files) == 37

    def test_chapter_information_rotte_no_omocha(self):
        URL = 'http://bato.to/reader#d647e1267a7c2c54'
        chapter = batoto.BatotoChapter.from_url(URL)
        assert chapter.alias == 'rotte-no-omocha'
        assert chapter.batoto_hash == 'd647e1267a7c2c54'
        assert chapter.chapter == '1'
        assert chapter.groups == ['Facepalm Scans']
        assert chapter.name == 'Rotte no Omocha!'
        assert chapter.title == '"A Candidate for the Princess\'s Harem!?"'
        path = os.path.join(
            self.directory.name, 'Rotte no Omocha',
            'Rotte no Omocha - c001 [Facepalm Scans].zip'
        )
        assert chapter.filename == path
        chapter.download()
        assert os.path.isfile(path) is True
        with zipfile.ZipFile(path) as chapter_zip:
            files = chapter_zip.infolist()
            assert len(files) == 38

    def test_chapter_information_tomochan(self):
        URL = 'http://bato.to/reader#cf03b01bd9e90ba8'
        config.get().cbz = True
        chapter = batoto.BatotoChapter.from_url(URL)
        assert chapter.alias == 'tomo-chan-wa-onna-no-ko'
        assert chapter.batoto_hash == 'cf03b01bd9e90ba8'
        assert chapter.chapter == '1-10'
        assert chapter.groups == ['M@STERSCANZ']
        assert chapter.name == 'Tomo-chan wa Onna no ko!'
        assert chapter.title is None
        path = os.path.join(
            self.directory.name, 'Tomo-chan wa Onna no ko',
            'Tomo-chan wa Onna no ko - c001-010 [MSTERSCANZ].cbz'
        )
        assert chapter.filename == path
        chapter.download()
        assert os.path.isfile(path) is True
        with zipfile.ZipFile(path) as chapter_zip:
            files = chapter_zip.infolist()
            assert len(files) == 10

    def test_chapter_unavailable_deleted(self):
        URL = 'http://bato.to/reader#ba173e587bdc9325'
        chapter = batoto.BatotoChapter(url=URL)
        assert chapter.available() is False

    def test_chapter_unavailable_old_url(self):
        URL = 'http://bato.to/read/_/203799/shokugeki-no-soma_ch46_by_casanova'
        chapter = batoto.BatotoChapter(url=URL)
        assert chapter.available() is False

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

    def test_series_molester_man(self):
        data = {'alias': 'molester-man',
                'chapters': ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10',
                             '11', '12', '13', '14', '14.5', '15', '16', '17',
                             '18', '19', '20', '21', '21.5'],
                'groups': ['Boon Scanlation'],
                'name': 'Molester Man',
                'url': 'http://bato.to/comic/_/comics/molester-man-r7471'}
        self.series_information_tester(data)

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
