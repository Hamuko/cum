from unittest import mock
import cumtest


class TestCLIUnfollow(cumtest.CumCLITest):
    def test_unfollow(self):
        FOLLOW = {'url': 'http://dynasty-scans.com/series/'
                         'inugami_san_and_nekoyama_san',
                  'alias': 'inugami-san-and-nekoyama-san',
                  'name': 'Inugami-san and Nekoyama-san'}
        MESSAGE = 'Removing follow for Inugami-san and Nekoyama-san'

        series = self.create_mock_series(**FOLLOW)
        series.follow()

        result = self.invoke('unfollow', 'inugami-san-and-nekoyama-san')
        db_series = self.db.session.query(self.db.Series).first()
        self.assertEqual(result.exit_code, 0)
        self.assertIn(MESSAGE, result.output)
        self.assertFalse(db_series.following)
