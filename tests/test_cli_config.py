from cum import config
import cumtest


class TestCLIConfig(cumtest.CumCLITest):
    @cumtest.skipIfNoBatotoLogin
    @cumtest.skipIfNoMadokamiLogin
    def test_config_get(self):
        MESSAGES = ['batoto.password = ' + config.get().batoto.password,
                    'batoto.username = ' + config.get().batoto.username,
                    'download_directory = ' + config.get().download_directory,
                    'madokami.password = ' + config.get().madokami.password,
                    'madokami.username = ' + config.get().madokami.username]

        result = self.invoke('config', 'get')
        self.assertEqual(result.exit_code, 0)
        for message in MESSAGES:
            self.assertIn(message, result.output)

    @cumtest.skipIfNoBatotoLogin
    def test_config_get_batoto_username(self):
        MESSAGE = 'batoto.username = ' + config.get().batoto.username

        result = self.invoke('config', 'get', 'batoto.username')
        self.assertEqual(result.exit_code, 0)
        self.assertIn(MESSAGE, result.output)

    def test_config_get_batoto_invalid_value(self):
        MESSAGE = 'Setting not found'

        result = self.invoke('config', 'get', 'batoto.wrongkey')
        self.assertEqual(result.exit_code, 1)
        self.assertIn(MESSAGE, result.output)

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

    def test_config_set_batoto_password(self):
        PASSWORD = 'password4testing'

        config.get().batoto.password = None
        config.get().write()

        result = self.invoke('config', 'set', 'batoto.password', PASSWORD)
        self.assertEqual(result.exit_code, 0)
        self.assertEqual(config.get().batoto.password, PASSWORD)

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
