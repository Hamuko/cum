from bs4 import BeautifulSoup
from cum import config, exceptions
from nose.tools import nottest
from urllib.parse import urljoin
from warnings import filterwarnings
import cumtest
import os
import requests
import unittest
import zipfile


class TestManganelo(cumtest.CumTest):
    MANGANELO_URL = 'https://manganelo.com/genre-all'

    def setUp(self):
        super().setUp()
        global manganelo
        filterwarnings(action = "ignore", message = "unclosed", category = ResourceWarning)
        from cum.scrapers import manganelo

    def tearDown(self):
        self.directory.cleanup()

    def get_five_latest_releases(self):
        r = requests.get(self.MANGANELO_URL)
        soup = BeautifulSoup(r.text, config.get().html_parser)
        chapters = soup.find_all("a", class_="genres-item-chap")
        links = [x["href"] for x in chapters]
        return links[:5]

    @nottest
    def series_information_tester(self, data):
        series = manganelo.ManganeloSeries(data['url'])
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
            self.assertIs(chapter.directory, None)
        self.assertEqual(len(data['chapters']), 0)

    # This test is disabled temporarily due to the architecture of
    # the chapter.from_url method, which assumes that if a chapter
    # exists then it will be listed on the series page.  Manganelo
    # seems to violate this assumption, in that there are chapters
    # which are accessible from the "latest chapters" page but which
    # are not listed on their respective series' pages, at least
    # not immediately.
    # TODO: come back to this test and find a way to construct a
    # chapter without requiring metadata from the series page
    def _test_chapter_download_latest(self):
        latest_releases = self.get_five_latest_releases()
        for release in latest_releases:
            try:
                chapter = manganelo.ManganeloChapter.from_url(release)
            except exceptions.ScrapingError as e:
                print('scraping error for {} - {}'.format(release, e))
                continue
            else:
                chapter.get(use_db=False)

    def test_chapter_filename_decimal(self):
        URL = "https://manganelo.com/chapter/citrus_saburo_uta/chapter_24.6"
        chapter = manganelo.ManganeloChapter.from_url(URL)
        path = os.path.join(self.directory.name, 'Citrus Saburo Uta',
                            'Citrus Saburo Uta - c024 x6 [Unknown].zip')
        self.assertEqual(chapter.chapter, '24.6')
        self.assertEqual(chapter.filename, path)

    def test_chapter_information_normal(self):
        URL = "https://manganelo.com/chapter/ramen_daisuki_koizumisan/chapter_18"
        chapter = manganelo.ManganeloChapter.from_url(URL)
        self.assertEqual(chapter.alias, 'ramen-daisuki-koizumi-san')
        self.assertTrue(chapter.available())
        self.assertEqual(chapter.chapter, '18')
        self.assertEqual(chapter.name, 'Ramen Daisuki Koizumi-San')
        self.assertEqual(chapter.title, 'Ramen Daisuki Koizumi-san Chapter 18')
        path = os.path.join(self.directory.name,
                            'Ramen Daisuki Koizumi-San',
                            'Ramen Daisuki Koizumi-San - c018 [Unknown].zip')
        self.assertEqual(chapter.filename, path)
        chapter.download()
        self.assertTrue(os.path.isfile(path))
        with zipfile.ZipFile(path) as chapter_zip:
            files = chapter_zip.infolist()
            self.assertEqual(len(files), 8)

    def test_chapter_information_chapterzero(self):
        URL = "https://manganelo.com/chapter/inu_to_hasami_wa_tsukaiyou/chapter_0"
        chapter = manganelo.ManganeloChapter.from_url(URL)
        self.assertEqual(chapter.alias, 'inu-to-hasami-wa-tsukaiyou')
        self.assertEqual(chapter.chapter, '0')
        self.assertEqual(chapter.name, 'Inu To Hasami Wa Tsukaiyou')
        self.assertEqual(chapter.title, 'Inu to Hasami wa Tsukaiyou Vol.1 Chapter 0')
        path = os.path.join(
            self.directory.name, 'Inu To Hasami Wa Tsukaiyou',
            'Inu To Hasami Wa Tsukaiyou - c000 [Unknown].zip')
        self.assertEqual(chapter.filename, path)
        chapter.download()
        self.assertTrue(os.path.isfile(path))
        with zipfile.ZipFile(path) as chapter_zip:
            files = chapter_zip.infolist()
            self.assertEqual(len(files), 32)

    def test_series_invalid(self):
        URL = "https://manganelo.com/manga/test_bad_manga_name"
        with self.assertRaises(exceptions.ScrapingError):
            series = manganelo.ManganeloSeries(url=URL)

    def test_chapter_unavailable(self):
        URL = "https://manganelo.com/chapter/oyasumi_punpun/chapter_999"
        chapter = manganelo.ManganeloChapter(url=URL)
        self.assertFalse(chapter.available())

    def test_series_oneword(self):
        data = {'alias': 'aria',
                'chapters': ['1', '2', '3', '4', '5', '6', '7', '8',
                             '9', '10', '10.5', '11', '12', '13', '14', '15',
                             '16', '17', '18', '19', '20', '21', '22', '23',
                             '24', '25', '26', '27', '28', '29', '30', '30.5',
                             '31', '32', '33', '34', '35', '35.5', '36',
                             '37', '37.5', '38', '39', '40', '41', '42', '43',
                             '44', '45', '45.5', '46', '47', '48', '49',
                             '50', '50.5', '51', '52', '53', '54', '55', '56',
                             '57', '57.5', '58', '59', '60', '60.1'],
                'name': 'Aria',
                'url': 'https://manganelo.com/manga/aria'}
        self.series_information_tester(data)

    def test_series_multiplewords(self):
        data = {'alias': 'prunus-girl',
                'chapters': ['1', '1.5', '2', '3', '4', '5', '5.5', '6', '7', '8',
                             '9', '10', '11', '11.5', '12', '13', '14', '15',
                             '16', '16.5', '17', '18', '19', '20', '21', '22',
                             '23', '24', '25', '26', '27', '28', '29', '30',
                             '31', '32', '32.5', '33', '34', '35', '36', '37',
                             '38', '39', '40', '41', '42', '42.5'],
                'name': 'Prunus Girl',
                'url': 'https://manganelo.com/manga/prunus_girl'}
        self.series_information_tester(data)

if __name__ == '__main__':
    unittest.main()
