from unittest import mock
import cumtest


class TestCLIOpen(cumtest.CumCLITest):
    def test_open(self):
        FOLLOW = {'url': 'http://bato.to/comic/_/comics/blood-r5840',
                  'alias': 'blood'}

        series = self.create_mock_series(**FOLLOW)
        series.follow()

        result = self.invoke('open', 'blood')
        self.assertEqual(result.exit_code, 0)
