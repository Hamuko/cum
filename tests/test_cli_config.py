from cum import config
from cum import exceptions
import cumtest


class TestCLIConfig(cumtest.CumCLITest):
    def test_config_corrupt(self):
        self.copy_broken_config()
        with self.assertRaises(exceptions.ConfigError):
            config.initialize(self.directory.name)

    def test_config_corrupt_output(self):
        MESSAGES = ['10:   "download_directory": "invalid",',
                    '11:   "madokami": {',
                    '12:     "password": "invalid",',
                    '13:     "username": "invalid"',
                    '14:     I am so broken',
                    '        ^',
                    '==> Error reading config: Expecting \',\' delimiter']

        self.copy_broken_config()
        result = self.invoke('config', 'initialise', self.directory.name)
        self.assertEqual(result.exit_code, 1)
        for message in MESSAGES:
            self.assertIn(message, result.output)

    @cumtest.skipIfNoMadokamiLogin
    def test_config_get(self):
        MESSAGES = ['download_directory = ' + config.get().download_directory,
                    'madokami.password = ' + config.get().madokami.password,
                    'madokami.username = ' + config.get().madokami.username]

        result = self.invoke('config', 'get')
        self.assertEqual(result.exit_code, 0)
        for message in MESSAGES:
            self.assertIn(message, result.output)

    def test_config_get_download_directory(self):
        MESSAGE = 'download_directory = ' + config.get().download_directory

        result = self.invoke('config', 'get', 'download_directory')
        self.assertEqual(result.exit_code, 0)
        self.assertIn(MESSAGE, result.output)

    def test_config_get_invalid_value(self):
        MESSAGE = 'Setting not found'

        result = self.invoke('config', 'get', 'wrongkey')
        self.assertEqual(result.exit_code, 1)
        self.assertIn(MESSAGE, result.output)

    def test_config_invalid_mode(self):
        MESSAGE = 'Mode must be either get or set'

        result = self.invoke('config', 'poke')
        self.assertEqual(result.exit_code, 1)
        self.assertIn(MESSAGE, result.output)

    def test_config_set_cbz(self):
        result = self.invoke('config', 'set', 'cbz', 'True')
        self.assertEqual(result.exit_code, 0)
        self.assertTrue(config.get().cbz)

    def test_config_set_cbz_false(self):
        config.get().cbz = True
        config.get().write()

        result = self.invoke('config', 'set', 'cbz', 'False')
        self.assertEqual(result.exit_code, 0)
        self.assertFalse(config.get().cbz)

    def test_config_set_invalid_setting(self):
        MESSAGE = 'Setting not found'

        result = self.invoke('config', 'set', 'cuterobots.sex', 'female')
        self.assertEqual(result.exit_code, 1)
        self.assertIn(MESSAGE, result.output)

    def test_config_set_invalid_subsetting(self):
        MESSAGE = 'Setting not found'

        result = self.invoke('config', 'set', 'batoto.trashing', 'True')
        self.assertEqual(result.exit_code, 1)
        self.assertIn(MESSAGE, result.output)

    def test_config_set_no_setting(self):
        MESSAGE = 'You must specify a setting'

        result = self.invoke('config', 'set')
        self.assertEqual(result.exit_code, 1)
        self.assertIn(MESSAGE, result.output)

    def test_config_set_no_value(self):
        MESSAGE = 'You must specify a value'

        result = self.invoke('config', 'set', 'batoto.username')
        self.assertEqual(result.exit_code, 1)
        self.assertIn(MESSAGE, result.output)

    def test_config_set_type_mismatch(self):
        MESSAGE = 'Type mismatch: value should be int'

        result = self.invoke('config', 'set', 'download_threads', 'seven')
        self.assertEqual(result.exit_code, 1)
        self.assertIn(MESSAGE, result.output)
