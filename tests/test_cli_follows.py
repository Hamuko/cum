from unittest import mock
import cumtest


class TestCLIFollows(cumtest.CumCLITest):
    def test_follows(self):
        FOLLOWS = [
            {'url': 'http://bato.to/comic/_/comics/b-gata-h-kei-r500',
             'alias': 'b-gata-h-kei'},
            {'url': 'http://bato.to/comic/_/comics/cerberus-r1588',
             'alias': 'cerberus'},
            {'url': 'http://bato.to/comic/_/comics/cromartie-highschool-r2189',
             'alias': 'cromartie-high-school'}
        ]

        for follow in FOLLOWS:
            series = self.create_mock_series(**follow)
            series.follow()

        result = self.invoke('follows')
        self.assertEqual(result.exit_code, 0)
        for follow in FOLLOWS:
            self.assertIn(follow['alias'], result.output)
