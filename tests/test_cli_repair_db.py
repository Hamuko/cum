from cum import sanity
import cumtest
import os


class TestCLIRepairDB(cumtest.CumCLITest):
    def test_repair_db(self):
        MESSAGES = ['Backing up database to cum.db.bak',
                    'Running database repair']

        self.copy_broken_database()
        backup_database = os.path.join(self.directory.name, 'cum.db.bak')

        result = self.invoke('repair-db')
        self.assertTrue(os.path.isfile(backup_database))
        self.assertEqual(result.exit_code, 0)
        for message in MESSAGES:
            self.assertIn(message, result.output)
        sanity_tester = sanity.DatabaseSanity(self.db.Base, self.db.engine)
        sanity_tester.test()
        self.assertTrue(sanity_tester.is_sane)
