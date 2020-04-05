from bs4 import BeautifulSoup
from cum import config, exceptions
from nose.tools import nottest
from urllib.parse import urljoin
import cumtest
import os
import requests
import unittest
import zipfile


class TestMangahere(cumtest.CumTest):
    MANGAHERE_URL = 'https://www.mangahere.cc/'

    def setUp(self):
        super().setUp()
        global mangahere
        from cum.scrapers import mangahere

    def tearDown(self):
        self.directory.cleanup()

    def get_five_latest_releases(self):
        r = requests.get(self.MANGAHERE_URL)
        soup = BeautifulSoup(r.text, config.get().html_parser)
        chapters = soup.find("ul", class_="manga-list-1-list").find_all("li")
        links = [urljoin(self.MANGAHERE_URL,
                         x.find("p", class_="manga-list-1-item-subtitle")
                         .find("a").get("href")) for x in chapters]
        return links[:5]

    @nottest
    def series_information_tester(self, data):
        series = mangahere.MangahereSeries(data['url'])
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

    # This test is disabled because I have discovered (via this test)
    # that for some series, the mobile links for chapters return 404s,
    # even the links on the actual mobile index page, making those
    # chapters unavailable via mobile.  Until I can get around to
    # reverse-engineering the obfuscation on the desktop site,
    # some series may not be able to be downloaded/followed.
    @nottest
    def test_chapter_download_latest(self):
        latest_releases = self.get_five_latest_releases()
        for release in latest_releases:
            try:
                chapter = mangahere.MangahereChapter.from_url(release)
            except exceptions.ScrapingError as e:
                print('scraping error for {} - {}'.format(release, e))
                continue
            else:
                chapter.get(use_db=False)

    def test_chapter_filename_decimal(self):
        URL = "https://www.mangahere.cc/manga/citrus_saburouta/"
        URL = "https://www.mangahere.cc/manga/citrus_saburouta/" + \
            "c020.5/1.html"
        chapter = mangahere.MangahereChapter.from_url(URL)
        path = os.path.join(self.directory.name, 'Citrus Saburouta',
                            'Citrus Saburouta - c020 x5 [Unknown].zip')
        self.assertEqual(chapter.chapter, '20.5')
        self.assertEqual(chapter.filename, path)

    def test_chapter_information_normal(self):
        URL = "https://www.mangahere.cc/manga/" + \
                "ramen_daisuki_koizumi_san/c018/1.html"
        chapter = mangahere.MangahereChapter.from_url(URL)
        self.assertEqual(chapter.alias, 'ramen-daisuki-koizumi-san')
        self.assertTrue(chapter.available())
        self.assertEqual(chapter.chapter, '18')
        self.assertEqual(chapter.name, 'Ramen Daisuki Koizumi san')
        self.assertEqual(chapter.title, 'Ch.018')
        path = os.path.join(self.directory.name,
                            'Ramen Daisuki Koizumi san',
                            'Ramen Daisuki Koizumi san - c018 [Unknown].zip')
        self.assertEqual(chapter.filename, path)
        chapter.download()
        self.assertTrue(os.path.isfile(path))
        with zipfile.ZipFile(path) as chapter_zip:
            files = chapter_zip.infolist()
            self.assertEqual(len(files), 8)

    def test_chapter_information_multidigit(self):
        URL = "https://www.mangahere.cc/manga/" + \
                "tsurezure_children/c192/1.html"
        chapter = mangahere.MangahereChapter.from_url(URL)
        self.assertEqual(chapter.alias, 'tsurezure-children')
        self.assertTrue(chapter.available())
        self.assertEqual(chapter.chapter, '192')
        self.assertEqual(chapter.name, 'Tsurezure Children')
        self.assertEqual(chapter.title, 'Ch.192')
        path = os.path.join(self.directory.name,
                            'Tsurezure Children',
                            'Tsurezure Children - c192 [Unknown].zip')
        self.assertEqual(chapter.filename, path)
        chapter.download()
        self.assertTrue(os.path.isfile(path))
        with zipfile.ZipFile(path) as chapter_zip:
            files = chapter_zip.infolist()
            self.assertEqual(len(files), 6)

    def test_chapter_information_chapterzero(self):
        URL = "https://www.mangahere.cc/manga/" + \
            "inu_to_hasami_wa_tsukaiyou/c000/1.html"
        chapter = mangahere.MangahereChapter.from_url(URL)
        self.assertEqual(chapter.alias, 'inu-to-hasami-wa-tsukaiyou')
        self.assertEqual(chapter.chapter, '0')
        self.assertEqual(chapter.name, 'Inu to Hasami wa Tsukaiyou')
        self.assertEqual(chapter.title, 'Ch.000')
        path = os.path.join(
            self.directory.name, 'Inu to Hasami wa Tsukaiyou',
            'Inu to Hasami wa Tsukaiyou - c000 [Unknown].zip')
        self.assertEqual(chapter.filename, path)
        chapter.download()
        self.assertTrue(os.path.isfile(path))
        with zipfile.ZipFile(path) as chapter_zip:
            files = chapter_zip.infolist()
            self.assertEqual(len(files), 32)

    def test_chapter_information_volume(self):
        URL = "https://www.mangahere.cc/manga/" + \
                "full_metal_alchemist/v026/c107/1.html"
        chapter = mangahere.MangahereChapter.from_url(URL)
        self.assertEqual(chapter.alias, 'full-metal-alchemist')
        self.assertEqual(chapter.chapter, '107')
        self.assertEqual(chapter.name, 'Full Metal Alchemist')
        self.assertEqual(chapter.title, 'Vol.026 Ch.107 - The Final Battle')
        path = os.path.join(
            self.directory.name, 'Full Metal Alchemist',
            'Full Metal Alchemist - c107 [Unknown].zip')
        self.assertEqual(chapter.filename, path)
        chapter.download()
        self.assertTrue(os.path.isfile(path))
        with zipfile.ZipFile(path) as chapter_zip:
            files = chapter_zip.infolist()
            self.assertEqual(len(files), 69)

    def test_chapter_information_volume_decimal(self):
        URL = "https://www.mangahere.cc/manga/" + \
            "ai_yori_aoshi/v16/c133.5/1.html"
        chapter = mangahere.MangahereChapter.from_url(URL)
        self.assertEqual(chapter.alias, 'ai-yori-aoshi')
        self.assertEqual(chapter.chapter, '133.5')
        self.assertEqual(chapter.name, 'Ai Yori Aoshi')
        self.assertEqual(chapter.title, 'Vol.16 Ch.133.5 - Special Chapter - Hanakotoba - Language of Flower')
        path = os.path.join(
            self.directory.name, 'Ai Yori Aoshi',
            'Ai Yori Aoshi - c133 x5 [Unknown].zip')
        self.assertEqual(chapter.filename, path)
        chapter.download()
        self.assertTrue(os.path.isfile(path))
        with zipfile.ZipFile(path) as chapter_zip:
            files = chapter_zip.infolist()
            self.assertEqual(len(files), 14)

    def test_series_invalid(self):
        URL = "https://www.mangahere.cc/manga/not_a_manga"
        with self.assertRaises(exceptions.ScrapingError):
            series = mangahere.MangahereSeries(url=URL)

    def test_chapter_unavailable_badvolume(self):
        URL = "https://www.mangahere.cc/manga/oyasumi_punpun/v99/c147/1.html"
        chapter = mangahere.MangahereChapter(url=URL)
        self.assertFalse(chapter.available())

    def test_chapter_unavailable_badchapter(self):
        URL = "https://www.mangahere.cc/manga/oyasumi_punpun/v09/c999/1.html"
        chapter = mangahere.MangahereChapter(url=URL)
        self.assertFalse(chapter.available())

    def test_chapter_unavailable_flatchapters(self):
        URL = "https://www.mangahere.cc/manga/nikoniko_x_punpun/c999/1.html"
        chapter = mangahere.MangahereChapter(url=URL)
        self.assertFalse(chapter.available())

    def test_series_flatchapters(self):
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
                'url': 'https://www.mangahere.cc/manga/aria'}
        self.series_information_tester(data)

    def test_series_volumes(self):
        data = {'alias': 'prunus-girl',
                'chapters': ['1', '1.5', '2', '3', '4',
                             '5', '5.5', '6', '7', '8',
                             '9', '10', '11', '11.5', '12',
                             '13', '14', '15', '14', '15',
                             '16', '17', '18', '19', '20',
                             '21', '22', '23', '24', '25',
                             '26', '27', '28', '29', '30',
                             '31', '32', '32.5', '33', '34',
                             '35', '36', '37', '38', '39',
                             '40', '41', '42', '42.5'],
                'name': 'Prunus Girl',
                'url': 'https://www.mangahere.cc/manga/prunus_girl'}
        self.series_information_tester(data)


if __name__ == '__main__':
    unittest.main()
