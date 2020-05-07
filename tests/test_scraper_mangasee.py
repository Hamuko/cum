from bs4 import BeautifulSoup
from cum import config, exceptions
from nose.tools import nottest
from urllib.parse import urljoin
import cumtest
import os
import requests
import unittest
import zipfile


class TestMangasee(cumtest.CumTest):
    MANGASEE_URL = 'https://mangaseeonline.us/'

    def setUp(self):
        super().setUp()
        global mangasee
        from cum.scrapers import mangasee

    def tearDown(self):
        self.directory.cleanup()

    def get_five_latest_releases(self):
        r = requests.get(self.MANGASEE_URL)
        soup = BeautifulSoup(r.text, config.get().html_parser)
        chapters = soup.find_all("a", class_="latestSeries")
        links = [urljoin(self.MANGASEE_URL, x.get("href")) for x in chapters]
        return links[:5]

    @nottest
    def series_information_tester(self, data):
        series = mangasee.MangaseeSeries(data['url'])
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

    def test_chapter_download_latest(self):
        latest_releases = self.get_five_latest_releases()
        for release in latest_releases:
            try:
                chapter = mangasee.MangaseeChapter.from_url(release)
            except exceptions.ScrapingError as e:
                print('scraping error for {} - {}'.format(release, e))
                continue
            else:
                chapter.get(use_db=False)

    def test_chapter_filename_decimal(self):
        URL = "https://mangaseeonline.us/read-online/" + \
            "Citrus-S-A-B-U-R-O-Uta-chapter-20.5-page-1.html"
        chapter = mangasee.MangaseeChapter.from_url(URL)
        path = os.path.join(self.directory.name, 'Citrus SABURO Uta',
                            'Citrus SABURO Uta - c020 x5 [Unknown].zip')
        self.assertEqual(chapter.chapter, '20.5')
        self.assertEqual(chapter.filename, path)

    def test_chapter_information_normal(self):
        URL = "https://mangaseeonline.us/read-online/" + \
            "Ramen-Daisuki-Koizumi-San-chapter-18-page-1.html"
        chapter = mangasee.MangaseeChapter.from_url(URL)
        self.assertEqual(chapter.alias, 'ramen-daisuki-koizumi-san')
        self.assertTrue(chapter.available())
        self.assertEqual(chapter.chapter, '18')
        self.assertEqual(chapter.name, 'Ramen Daisuki Koizumi-san')
        self.assertEqual(chapter.title, 'Chapter 18')
        path = os.path.join(self.directory.name,
                            'Ramen Daisuki Koizumi-san',
                            'Ramen Daisuki Koizumi-san - c018 [Unknown].zip')
        self.assertEqual(chapter.filename, path)
        chapter.download()
        self.assertTrue(os.path.isfile(path))
        with zipfile.ZipFile(path) as chapter_zip:
            files = chapter_zip.infolist()
            self.assertEqual(len(files), 8)

    def test_chapter_information_chapterzero(self):
        URL = "https://mangaseeonline.us/read-online/" + \
            "Inu-To-Hasami-Wa-Tsukaiyou-chapter-0-page-1.html"
        chapter = mangasee.MangaseeChapter.from_url(URL)
        self.assertEqual(chapter.alias, 'inu-to-hasami-wa-tsukaiyou')
        self.assertEqual(chapter.chapter, '0')
        self.assertEqual(chapter.name, 'Inu to Hasami wa Tsukaiyou')
        self.assertEqual(chapter.title, 'Chapter 0')
        path = os.path.join(
            self.directory.name, 'Inu to Hasami wa Tsukaiyou',
            'Inu to Hasami wa Tsukaiyou - c000 [Unknown].zip')
        self.assertEqual(chapter.filename, path)
        chapter.download()
        self.assertTrue(os.path.isfile(path))
        with zipfile.ZipFile(path) as chapter_zip:
            files = chapter_zip.infolist()
            self.assertEqual(len(files), 51)

    def test_chapter_information_multiseason(self):
        URL = "https://mangaseeonline.us/read-online/" + \
            "Kubera-chapter-3-index-2-page-1.html"
        chapter = mangasee.MangaseeChapter.from_url(URL)
        self.assertEqual(chapter.alias, 'kubera')
        self.assertEqual(chapter.chapter, '02.003')
        self.assertEqual(chapter.name, 'Kubera')
        self.assertEqual(chapter.title, 'S2 - Chapter 3')
        path = os.path.join(
            self.directory.name, 'Kubera',
            'Kubera - c002 x003 [Unknown].zip')
        self.assertEqual(chapter.filename, path)
        chapter.download()
        self.assertTrue(os.path.isfile(path))
        with zipfile.ZipFile(path) as chapter_zip:
            files = chapter_zip.infolist()
            self.assertEqual(len(files), 39)

    def test_chapter_information_multiseason_decimal(self):
        URL = "https://mangaseeonline.us/read-online/" + \
            "Kubera-chapter-164.5-index-2-page-1.html"
        chapter = mangasee.MangaseeChapter.from_url(URL)
        self.assertEqual(chapter.alias, 'kubera')
        self.assertEqual(chapter.chapter, '02.164.5')
        self.assertEqual(chapter.name, 'Kubera')
        self.assertEqual(chapter.title, 'S2 - Chapter 164.5')
        path = os.path.join(
            self.directory.name, 'Kubera',
            'Kubera - c002 x164.5 [Unknown].zip')
        self.assertEqual(chapter.filename, path)
        chapter.download()
        self.assertTrue(os.path.isfile(path))
        with zipfile.ZipFile(path) as chapter_zip:
            files = chapter_zip.infolist()
            self.assertEqual(len(files), 45)

    def test_series_invalid(self):
        URL = "https://mangaseeonline.us/read-online/" + \
            "not_a_manga"
        with self.assertRaises(exceptions.ScrapingError):
            series = mangasee.MangaseeSeries(url=URL)

    def test_chapter_unavailable(self):
        URL = "https://mangaseeonline.us/read-online/" + \
            "Oyasumi-Punpun-chapter-999-page-1.html"
        chapter = mangasee.MangaseeChapter(url=URL)
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
                             '57', '57.5', '58', '59', '60', '60.5'],
                'name': 'Aria',
                'url': 'https://mangaseeonline.us/manga/Aria'}
        self.series_information_tester(data)

    def test_series_multiplewords(self):
        data = {'alias': 'prunus-girl',
                'chapters': ['1', '2', '3', '4', '5', '6', '7', '8',
                             '9', '10', '11', '12', '13', '14', '15',
                             '16', '17', '18', '19', '20', '21', '22',
                             '23', '24', '25', '26', '27', '28', '29', '30',
                             '31', '32', '32.5', '33', '34', '35', '36', '37',
                             '38', '39', '40', '41', '42', '43'],
                'name': 'Prunus Girl',
                'url': 'https://mangaseeonline.us/manga/Prunus-Girl'}
        self.series_information_tester(data)


if __name__ == '__main__':
    unittest.main()
