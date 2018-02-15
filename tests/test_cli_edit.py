from unittest import mock
import cumtest


class TestCLIEdit(cumtest.CumCLITest):
    FOLLOW = {'url': ('https://manga.madokami.al/Manga/M/MO/MOLE/'
                      'Molester%20Man'),
              'alias': 'molester-man', 'name': 'Molester Man'}

    def setUp(self):
        super().setUp()
        series = self.create_mock_series(**TestCLIEdit.FOLLOW)
        series.follow()

    def test_edit_alias(self):
        ALIAS_NEW = 'molester'
        MESSAGE = 'Changed alias for molester-man to molester'

        args = ('edit', TestCLIEdit.FOLLOW['alias'], 'alias', ALIAS_NEW)
        result = self.invoke(*args)
        self.assertEqual(result.exit_code, 0)
        self.assertIn(MESSAGE, result.output)

        series = self.db.session.query(self.db.Series).get(1)
        self.assertEqual(series.alias, ALIAS_NEW)

    def test_edit_alias_illegal_value_none(self):
        ALIAS_NEW = 'none'
        MESSAGE = 'Illegal value none'

        args = ('edit', TestCLIEdit.FOLLOW['alias'], 'alias', ALIAS_NEW)
        result = self.invoke(*args)

        args = ('edit', TestCLIEdit.FOLLOW['alias'], 'alias', ALIAS_NEW)
        result = self.invoke(*args)
        self.assertEqual(result.exit_code, 1)
        self.assertIn(MESSAGE, result.output)

        series = self.db.session.query(self.db.Series).get(1)
        self.assertEqual(series.alias, TestCLIEdit.FOLLOW['alias'])

    def test_edit_directory(self):
        DIR_NEW = 'molesterdir'
        MESSAGE = 'Changed directory for molester-man to molesterdir'

        args = ('edit', TestCLIEdit.FOLLOW['alias'], 'directory', DIR_NEW)
        result = self.invoke(*args)
        self.assertEqual(result.exit_code, 0)
        self.assertIn(MESSAGE, result.output)

        series = self.db.session.query(self.db.Series).get(1)
        self.assertEqual(series.directory, DIR_NEW)

    def test_edit_invalid_setting(self):
        MESSAGE = 'Invalid setting rating'

        args = ('edit', TestCLIEdit.FOLLOW['alias'], 'rating', '10/10')
        result = self.invoke(*args)
        self.assertEqual(result.exit_code, 1)
        self.assertIn(MESSAGE, result.output)
