from unittest import mock
import cumtest


class TestCLIOpen(cumtest.CumCLITest):
    def test_open(self):
        FOLLOW = {'url': 'https://manga.madokami.al/Manga/B/BL/BLOO/Blood%2B',
                  'alias': 'blood'}

        series = self.create_mock_series(**FOLLOW)
        series.follow()

        result = self.invoke('open', 'blood')
        self.assertEqual(result.exit_code, 0)
