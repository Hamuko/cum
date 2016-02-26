from click.testing import CliRunner
from cum import config, cum, sanity
from shutil import copyfile
import os
import tempfile
import unittest


class TestCLI(unittest.TestCase):
    def setUp(self):
        global db, scrapers
        self.directory = tempfile.TemporaryDirectory()
        self.runner = CliRunner()
        config.initialize(self.directory.name)
        c = config.get()
        c.batoto.password = os.environ['BATOTO_PASSWORD']
        c.batoto.username = os.environ['BATOTO_USERNAME']
        c.download_directory = self.directory.name
        c.madokami.password = os.environ['MADOKAMI_PASSWORD']
        c.madokami.username = os.environ['MADOKAMI_USERNAME']
        c.write()
        from cum import db, scrapers
        db.initialize()

    def tearDown(self):
        self.directory.cleanup()

    def copy_broken_database(self):
        """Copies a pre-defined broken database into the current directory."""
        test_directory = os.path.dirname(os.path.realpath(__file__))
        broken_db_path = os.path.join(test_directory, 'broken_database.db')
        target_db_path = os.path.join(self.directory.name, 'cum.db')
        copyfile(broken_db_path, target_db_path)

    def invoke(self, *arguments, **kwargs):
        """Alias for the CliRunner invoke using default arguments needed for testing.
        """
        default_args = ['--cum-directory', self.directory.name]
        args = default_args + list(arguments)
        return self.runner.invoke(cum.cli, args, **kwargs)

    def test_alias(self):
        ALIAS_NEW = 'molester'
        ALIAS_OLD = 'molester-man'
        MESSAGE = 'Changing alias "molester-man" to "molester"'
        URL = 'http://bato.to/comic/_/comics/molester-man-r7471'

        series = scrapers.BatotoSeries(URL)
        assert series.alias == ALIAS_OLD
        series.follow()

        result = self.invoke('alias', ALIAS_OLD, ALIAS_NEW)
        series = db.session.query(db.Series).get(1)
        assert series.alias == ALIAS_NEW
        assert result.exit_code == 0
        assert MESSAGE in result.output

    def test_chapters(self):
        URL = 'http://bato.to/comic/_/comics/date-a-live-r4555'
        MESSAGES = [
            'f  chapter  title [group]',
            '         1  Date 1 - Spirit [Village Idiot]',
            'i        2  Date 2 - Method [Village Idiot]',
            'n        3  Date 3 - Training [Village Idiot]',
            'n        4  Date 4 - Encounter [Village Idiot]',
            'n        5  Date 5 - Tohka [Village Idiot]',
            'n        6  Date 6 - Battle Commence! [End] [Village Idiot]'
        ]

        series = scrapers.BatotoSeries(URL)
        series.follow()

        chapter_1 = db.session.query(db.Chapter).filter_by(chapter='1').one()
        chapter_2 = db.session.query(db.Chapter).filter_by(chapter='2').one()
        chapter_1.downloaded = 1
        chapter_2.downloaded = -1
        db.session.commit()

        result = self.invoke('chapters', 'date-a-live')
        assert result.exit_code == 0
        for message in MESSAGES:
            assert message in result.output

    def test_download(self):
        URLS = ['http://bato.to/comic/_/comics/goodbye-body-r13725',
                'http://bato.to/comic/_/comics/green-beans-r15344']
        FILENAMES = ['Goodbye Body/Goodbye Body - c000 [Bird Collective '
                     'Translations].zip',
                     'Green Beans/Green Beans - c000 [Kotonoha].zip']
        MESSAGES = ['goodbye-body 0', 'green-beans 0']

        for url in URLS:
            series = scrapers.BatotoSeries(url)
            series.follow()

        result = self.invoke('download')
        assert result.exit_code == 0
        for message in MESSAGES:
            assert message in result.output
        for filename in FILENAMES:
            path = os.path.join(self.directory.name, filename)
            assert os.path.isfile(path) is True

    def test_download_alias(self):
        URLS = ['http://bato.to/comic/_/comics/goodbye-body-r13725',
                'http://bato.to/comic/_/comics/green-beans-r15344']
        FILENAME = 'Green Beans/Green Beans - c000 [Kotonoha].zip'
        MESSAGE = 'green-beans 0'
        NOT_MESSAGE = 'goodbye-body 0'

        for url in URLS:
            series = scrapers.BatotoSeries(url)
            series.follow()

        result = self.invoke('download', 'green-beans')
        assert result.exit_code == 0
        assert MESSAGE in result.output
        assert NOT_MESSAGE not in result.output
        assert os.path.isfile(os.path.join(self.directory.name,
                                           FILENAME)) is True

    def test_follow_batoto(self):
        URL = 'http://bato.to/comic/_/comics/akuma-no-riddle-r9759'
        MESSAGE = 'Adding follow for Akuma no Riddle (akuma-no-riddle)'

        series = scrapers.series_by_url('http://www.google.com')

        result = self.invoke('follow', URL)
        assert result.exit_code == 0
        assert MESSAGE in result.output

    def test_follow_batoto_duplicate(self):
        URL = 'http://bato.to/comic/_/comics/akuma-no-riddle-r9759'
        MESSAGES = ['Adding follow for Akuma no Riddle (akuma-no-riddle)',
                    'You are already following this series']

        series = scrapers.BatotoSeries(URL)
        series.follow()

        result = self.invoke('follow', URL)
        assert result.exit_code == 0
        for message in MESSAGES:
            assert message in result.output

    def test_follow_batoto_download(self):
        URL = 'http://bato.to/comic/_/comics/dog-days-r6928'
        FILENAMES = ['Dog Days - c000 [CXC Scans].zip',
                     'Dog Days - c001 [CXC Scans].zip',
                     'Dog Days - c002 [CXC Scans].zip',
                     'Dog Days - c003 [CXC Scans].zip',
                     'Dog Days - c004 [CXC Scans].zip']
        MESSAGES = ['Adding follow for Dog Days (dog-days)',
                    'Downloading 5 chapters']

        result = self.invoke('follow', URL, '--download')
        files = [os.path.join(self.directory.name, 'Dog Days', x)
                 for x in FILENAMES]
        assert result.exit_code == 0
        for message in MESSAGES:
            assert message in result.output
        for file in files:
            assert os.path.isfile(file) is True

    def test_follow_batoto_ignore(self):
        URL = 'http://bato.to/comic/_/comics/dog-days-r6928'
        MESSAGES = ['Adding follow for Dog Days (dog-days)',
                    'Ignoring 5 chapters']

        result = self.invoke('follow', URL, '--ignore')
        chapters = db.session.query(db.Chapter).all()
        assert result.exit_code == 0
        for message in MESSAGES:
            assert message in result.output
        for chapter in chapters:
            assert chapter.downloaded == -1

    def test_follow_dynastyscans(self):
        URL = 'http://dynasty-scans.com/series/akuma_no_riddle'
        MESSAGE = 'Adding follow for Akuma no Riddle (akuma-no-riddle)'

        result = self.invoke('follow', URL)
        assert result.exit_code == 0
        assert MESSAGE in result.output

    def test_follow_invalid(self):
        URL = 'http://www.google.com'
        MESSAGE = 'Invalid URL "{}"'.format(URL)

        result = self.invoke('follow', URL)
        assert result.exit_code == 0
        assert MESSAGE in result.output

    def test_follow_madokami(self):
        URL = 'https://manga.madokami.com/Manga/A/AK/AKUM/Akuma%20no%20Riddle'
        MESSAGE = 'Adding follow for Akuma no Riddle (akuma-no-riddle)'

        result = self.invoke('follow', URL)
        assert result.exit_code == 0
        assert MESSAGE in result.output

    def test_follows(self):
        URLS = ['http://bato.to/comic/_/comics/b-gata-h-kei-r500',
                'http://bato.to/comic/_/comics/cerberus-r1588',
                'http://bato.to/comic/_/comics/cromartie-high-school-r2189']
        ALIASES = ['b-gata-h-kei', 'cerberus', 'cromartie-high-school']

        for url in URLS:
            series = scrapers.BatotoSeries(url)
            series.follow()

        result = self.invoke('follows')
        assert result.exit_code == 0
        for alias in ALIASES:
            assert alias in result.output

    def test_get_alias_invalid(self):
        MESSAGE = 'Invalid selection "alias,1"'

        result = self.invoke('get', 'alias,1')
        assert result.exit_code == 0
        assert MESSAGE in result.output

    def test_get_alias_batoto(self):
        URL = 'http://bato.to/comic/_/comics/girls-go-around-r9856'
        MESSAGE = 'girls-go-around 5'

        series = scrapers.BatotoSeries(URL)
        series.follow()
        path = os.path.join(self.directory.name, 'Girls Go Around',
                            'Girls Go Around - c005 [Underdog Scans].zip')

        result = self.invoke('get', 'girls-go-around:5')
        assert result.exit_code == 0
        assert MESSAGE in result.output
        assert os.path.isfile(path) is True

    def test_get_chapter_batoto(self):
        URL = 'http://bato.to/reader#ac0a859633965a8e'
        MESSAGE = 'g-koike-keiichi 0'

        path = os.path.join(self.directory.name, 'G KOIKE Keiichi',
                            'G KOIKE Keiichi - c000 [Gantz_Waitingroom].zip')
        result = self.invoke('get', URL)
        assert result.exit_code == 0
        assert MESSAGE in result.output
        assert os.path.isfile(path) is True

    def test_get_series_batoto(self):
        URL = 'http://bato.to/comic/_/comics/gekkou-spice-r2863'
        FILENAMES = ['Gekkou Spice - c001 [Osuwari Team].zip',
                     'Gekkou Spice - c002 [Aerandria Scans].zip',
                     'Gekkou Spice - c003 [Aerandria Scans].zip',
                     'Gekkou Spice - c004 [Sweet Lunacy].zip']
        MESSAGES = ['gekkou-spice 4', 'gekkou-spice 3',
                    'gekkou-spice 2', 'gekkou-spice 1']

        files = [os.path.join(self.directory.name, 'Gekkou Spice', x)
                 for x in FILENAMES]
        result = self.invoke('get', URL)
        assert result.exit_code == 0
        for message in MESSAGES:
            assert message in result.output
        for file in files:
            assert os.path.isfile(file) is True

    def test_ignore(self):
        URL = 'http://bato.to/comic/_/eien-no-mae-r8817'
        MESSAGE = 'Ignored chapter 0 for Eien no Mae'

        series = scrapers.BatotoSeries(URL)
        series.follow()

        result = self.invoke('ignore', 'eien-no-mae', '0')
        chapter = db.session.query(db.Chapter).first()
        assert result.exit_code == 0
        assert MESSAGE in result.output
        assert chapter.downloaded == -1

    def test_ignore_all(self):
        URL = 'http://bato.to/comic/_/comics/fetish-r1133'
        MESSAGE = 'Ignored 5 chapters for Fetish'

        series = scrapers.BatotoSeries(URL)
        series.follow()

        result = self.invoke('ignore', 'fetish', 'all', input='y')
        chapters = db.session.query(db.Chapter).all()
        assert result.exit_code == 0
        assert MESSAGE in result.output
        for chapter in chapters:
            assert chapter.downloaded == -1

    def test_new(self):
        URL = 'http://bato.to/comic/_/comics/blood-r5840'
        MESSAGES = ['blood', '1-4  5-8  9-12  13-16  17-20']

        series = scrapers.BatotoSeries(URL)
        series.follow()

        result = self.invoke('new')
        assert result.exit_code == 0
        for message in MESSAGES:
            assert message in result.output

    def test_new_compact(self):
        URL = 'http://bato.to/comic/_/comics/blood-r5840'
        MESSAGE = 'blood 1-4  5-8  9-12  13-16  17-20'

        config.get().compact_new = True
        series = scrapers.BatotoSeries(URL)
        series.follow()

        result = self.invoke('new')
        assert result.exit_code == 0
        assert MESSAGE in result.output

    def test_new_broken_database(self):
        MESSAGES = ['groups table is missing from database',
                    'chapters.title column has inappropriate datatype INTEGER '
                    '(should be VARCHAR)',
                    'series.directory column is missing from database',
                    'Database has failed sanity check; run `cum repair-db` to '
                    'repair database']

        self.copy_broken_database()

        result = self.invoke('new')
        assert result.exit_code == 1
        for message in MESSAGES:
            assert message in result.output

    def test_open(self):
        URL = 'http://bato.to/comic/_/comics/blood-r5840'

        series = scrapers.BatotoSeries(URL)
        series.follow()
        result = self.invoke('open', 'blood')
        assert result.exit_code == 0

    def test_repair_db(self):
        MESSAGES = ['Backing up database to cum.db.bak',
                    'Running database repair']

        self.copy_broken_database()
        backup_database = os.path.join(self.directory.name, 'cum.db.bak')

        result = self.invoke('repair-db')
        assert os.path.isfile(backup_database) is True
        assert result.exit_code == 0
        for message in MESSAGES:
            assert message in result.output
        sanity_tester = sanity.DatabaseSanity(db.Base, db.engine)
        sanity_tester.test()
        assert sanity_tester.is_sane is True

    def test_unfollow(self):
        URL = 'http://dynasty-scans.com/series/inugami_san_and_nekoyama_san'
        MESSAGE = 'Removing follow for Inugami-san and Nekoyama-san'

        series = scrapers.DynastyScansSeries(URL)
        series.follow()

        result = self.invoke('unfollow', 'inugami-san-and-nekoyama-san')
        db_series = db.session.query(db.Series).first()
        assert result.exit_code == 0
        assert MESSAGE in result.output
        assert db_series.following is False

    def test_unignore(self):
        URL = 'http://bato.to/comic/_/eien-no-mae-r8817'
        MESSAGE = 'Unignored chapter 0 for Eien no Mae'

        series = scrapers.BatotoSeries(URL)
        series.follow()

        chapter = db.session.query(db.Chapter).first()
        chapter.downloaded = -1
        db.session.commit()

        result = self.invoke('unignore', 'eien-no-mae', '0')
        chapter = db.session.query(db.Chapter).first()
        assert result.exit_code == 0
        assert MESSAGE in result.output
        assert chapter.downloaded == 0

    def test_unignore_all(self):
        URL = 'http://bato.to/comic/_/comics/fetish-r1133'
        MESSAGE = 'Unignored 5 chapters for Fetish'

        series = scrapers.BatotoSeries(URL)
        series.follow()
        chapters = db.session.query(db.Chapter).all()
        for chapter in chapters:
            chapter.downloaded = -1
        db.session.commit()

        result = self.invoke('unignore', 'fetish', 'all', input='y')
        chapters = db.session.query(db.Chapter).all()
        assert result.exit_code == 0
        assert MESSAGE in result.output
        for chapter in chapters:
            assert chapter.downloaded == 0

    def test_update(self):
        URL = 'http://bato.to/comic/_/comics/femme-fatale-r468'
        MESSAGES = ['Updating 1 series',
                    'femme-fatale',
                    '1  2  3  4  4.5  5  6  7  8  8.5  9  10  11  12']

        series = scrapers.BatotoSeries(URL)
        series.follow()
        chapters = db.session.query(db.Chapter).all()
        for chapter in chapters:
            db.session.delete(chapter)
        db.session.commit()
        chapters = db.session.query(db.Chapter).all()
        assert len(chapters) == 0

        result = self.invoke('update')
        chapters = db.session.query(db.Chapter).all()
        assert result.exit_code == 0
        for message in MESSAGES:
            assert message in result.output
        assert len(chapters) == 14

if __name__ == '__main__':
    unittest.main()
