from unittest import mock
import cumtest


class TestCLIAlias(cumtest.CumCLITest):
    def test_alias(self):
        FOLLOW = {'url': 'http://bato.to/comic/_/comics/molester-man-r7471',
                  'alias': 'molester-man', 'name': 'Molester Man'}
        ALIAS_NEW = 'molester'
        MESSAGE = 'Changing alias "molester-man" to "molester"'

        series = self.create_mock_series(**FOLLOW)
        series.follow()

        result = self.invoke('alias', FOLLOW['alias'], ALIAS_NEW)
        series = self.db.session.query(self.db.Series).get(1)
        self.assertEqual(series.alias, ALIAS_NEW)
        self.assertEqual(result.exit_code, 0)
        self.assertIn(MESSAGE, result.output)
