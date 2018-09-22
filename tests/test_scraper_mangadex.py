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

def language_filter(a):
    try:
        regex = re.compile(r'/images/flags/')
        return a.find_parent('tr').find('img', src=regex)['title'] == 'English'
    # ignore chapter links that do not state a language
    except TypeError:
        return None

class TestMangadex(cumtest.CumTest):
    MANGADEX_URL = 'https://mangadex.org/'

    def setUp(self):
        super().setUp()
        global mangadex
        from cum.scrapers import mangadex

    def tearDown(self):
        self.directory.cleanup()


    def get_five_latest_releases(self):
        r = requests.get(self.MANGADEX_URL + 'updates')
        soup = BeautifulSoup(r.text, config.get().html_parser)
        chapters = soup.find_all('a', href=mangadex.MangadexChapter.url_re)
        chapters = [a for a in chapters if language_filter(a)]
        links = [urljoin(self.MANGADEX_URL, x.get('href')) for x in chapters]
        return links[:5]

    def series_information_tester(self, data):
        series = mangadex.MangadexSeries(data['url'])
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

    def test_chapter_download_latest(self):
        latest_releases = self.get_five_latest_releases()
        for release in latest_releases:
            try:
                chapter = mangadex.MangadexChapter.from_url(release)
            except exceptions.ScrapingError as e:
                print('scrapping error for {} - {}'.format(release, e))
                continue
            else:
                chapter.get(use_db=False)

    def test_chapter_filename_decimal(self):
        URL = 'https://mangadex.org/chapter/24779'
        chapter = mangadex.MangadexChapter.from_url(URL)
        path = os.path.join(
            self.directory.name, 'Citrus',
            'Citrus - c020 x9 [Chaosteam].zip'
        )
        self.assertEqual(chapter.chapter, '20.9')
        self.assertEqual(chapter.filename, path)

    def test_chapter_filename_version2(self):
        # 1v2 style version numbers seem to be omitted on the current site
        URL = 'https://mangadex.org/chapter/12361'
        chapter = mangadex.MangadexChapter.from_url(URL)
        path = os.path.join(
            self.directory.name, 'Urara Meirochou',
            'Urara Meirochou - c001 [Kyakka].zip'
        )
        self.assertEqual(chapter.chapter, '1')
        self.assertEqual(chapter.filename, path)

    def test_chapter_information_ramen_daisuki_koizumi_san(self):
        URL = 'https://mangadex.org/chapter/26441'
        chapter = mangadex.MangadexChapter.from_url(URL)
        self.assertEqual(chapter.alias, 'ramen-daisuki-koizumi-san')
        self.assertTrue(chapter.available())
        self.assertEqual(chapter.chapter, '18')
        self.assertEqual(chapter.groups, ['Saiko Scans'])
        self.assertEqual(chapter.name, 'Ramen Daisuki Koizumi-san')
        self.assertEqual(chapter.title, 'Strange-flavored Ramen')
        path = os.path.join(self.directory.name,
                            'Ramen Daisuki Koizumi-san',
                            'Ramen Daisuki Koizumi-san - c018 [Saiko Scans].zip')
        self.assertEqual(chapter.filename, path)
        chapter.download()
        self.assertTrue(os.path.isfile(path))
        with zipfile.ZipFile(path) as chapter_zip:
            files = chapter_zip.infolist()
            self.assertEqual(len(files), 8)

    def test_chapter_information_hidamari_sketch(self):
        URL = 'https://mangadex.org/chapter/9833'
        chapter = mangadex.MangadexChapter.from_url(URL)
        self.assertEqual(chapter.alias, 'hidamari-sketch')
        self.assertEqual(chapter.chapter, '0')
        self.assertEqual(chapter.groups, ['Highlanders'])
        self.assertEqual(chapter.name, 'Hidamari Sketch')
        self.assertEqual(chapter.title, None)
        path = os.path.join(
            self.directory.name, 'Hidamari Sketch',
            'Hidamari Sketch - c000 [Highlanders].zip'
        )
        self.assertEqual(chapter.filename, path)
        chapter.download()
        self.assertTrue(os.path.isfile(path))
        with zipfile.ZipFile(path) as chapter_zip:
            files = chapter_zip.infolist()
            self.assertEqual(len(files), 11)

    def test_chapter_information_tomochan(self):
        URL = 'https://mangadex.org/chapter/28082'
        config.get().cbz = True
        chapter = mangadex.MangadexChapter.from_url(URL)
        self.assertEqual(chapter.alias, 'tomo-chan-wa-onna-no-ko')
        self.assertEqual(chapter.chapter, '1')
        self.assertEqual(chapter.groups, ['M@STER Scans'])
        self.assertEqual(chapter.name, 'Tomo-chan wa Onna no ko!')
        self.assertEqual(chapter.title, 'Once In A Life Time Misfire')
        path = os.path.join(
            self.directory.name, 'Tomo-chan wa Onna no ko',
            'Tomo-chan wa Onna no ko - c001 [MSTER Scans].cbz'
        )
        self.assertEqual(chapter.filename, path)
        chapter.download()
        self.assertTrue(os.path.isfile(path))
        with zipfile.ZipFile(path) as chapter_zip:
            files = chapter_zip.infolist()
            self.assertEqual(len(files), 1)

    def test_chapter_unavailable(self):
        URL = ''.join(['https://mangadex.org/chapter/',
                       '9999999999999999999999999999999999999999999999',
                       '99999999999999999999999'])
        chapter = mangadex.MangadexChapter(url=URL)
        self.assertFalse(chapter.available())

    def test_series_aria(self):
        data = {'alias': 'aria',
                'chapters': ['1', '2', '3', '4', '5', '6', '7', '7.5', '8',
                             '9', '10', '11', '12', '13', '14', '15', '16',
                             '17', '18', '19', '20', '21', '22', '23', '24',
                             '25', '26', '27', '28', '29', '30', '30.5', '31',
                             '32', '33', '34', '35', '35.5', '36', '37',
                             '37.5', '38', '39', '40', '41', '42', '43', '44',
                             '45', '45.5', '46', '47', '48', '49', '50',
                             '50.5', '51', '52', '53', '54', '55', '56', '57',
                             '57.5', '58', '59', '60', '60.5'],
                'groups': ['promfret', 'Amano Centric Scans'],
                'name': 'Aria',
                'url': 'https://mangadex.org/manga/2007'}
        self.series_information_tester(data)

    def test_series_prunus_girl(self):
        data = {'alias': 'prunus-girl',
                'chapters': ['1', '2', '3', '4', '5', '6', '6.5', '7', '8',
                             '9', '10', '11', '11.5', '12', '13', '14', '15',
                             '16', '16.5', '17', '18', '19', '20', '21', '22',
                             '23', '24', '25', '26', '27', '28', '29', '30',
                             '31', '32', '32.5', '33', '34', '35', '36', '37',
                             '38', '39', '40', '41', '42', '43'],
                'groups': ['Unknown', 'WOW!Scans', 'Maigo'],
                'name': 'Prunus Girl',
                'url': 'https://mangadex.org/manga/18'}
        self.series_information_tester(data)

    def test_series_no_chapters(self):
        data = {'alias': 'yorumori-no-kuni-no-sora-ni',
                'chapters': [],
                'groups': [],
                'name': 'Yorumori no Kuni no Sora ni',
                'url': 'https://mangadex.org/manga/13004'}
        self.series_information_tester(data)

if __name__ == '__main__':
    unittest.main()
