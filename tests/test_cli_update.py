from cum import config
from unittest import mock
import cumtest


class TestCLIUpdate(cumtest.CumCLITest):
    @cumtest.skipIfNoBatotoLogin
    def test_update(self):
        FOLLOWS = [
            {'url': 'http://bato.to/comic/_/comics/femme-fatale-r468',
             'alias': 'femme-fatale', 'name': 'Femme Fatale'},
            {'url': 'http://bato.to/comic/_/comics/houkago-r9187',
             'alias': 'houkago', 'name': 'Houkago'}
        ]
        MESSAGES = [
            'Updating 2 series',
            'femme-fatale 1  2  3  4  4.5  5  6  7  8  8.5  9  10  11  12',
            'houkago      1  2'
        ]

        config.get().compact_new = True
        config.get().write()

        for follow in FOLLOWS:
            series = self.create_mock_series(**follow)
            series.follow()
        chapters = self.db.session.query(self.db.Chapter).all()
        self.assertEqual(len(chapters), 0)

        result = self.invoke('update')
        chapters = self.db.session.query(self.db.Chapter).all()
        self.assertEqual(result.exit_code, 0)
        for message in MESSAGES:
            self.assertIn(message, result.output)
        self.assertEqual(len(chapters), 16)

    def test_update_invalid_login(self):
        FOLLOW = {'url': 'http://bato.to/comic/_/comics/femme-fatale-r468',
                  'alias': 'femme-fatale', 'name': 'Femme Fatale'}
        MESSAGE = 'Unable to update femme-fatale (Batoto login error)'

        series = self.create_mock_series(**FOLLOW)
        series.follow()

        config.get().batoto.cookie = None
        config.get().batoto.member_id = None
        config.get().batoto.pass_hash = None
        config.get().batoto.password = 'Notvalid'
        config.get().batoto.username = 'Notvalid'
        config.get().write()

        result = self.invoke('update')
        self.assertEqual(result.exit_code, 0)
        self.assertIn(MESSAGE, result.output)
