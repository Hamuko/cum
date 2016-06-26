from click.testing import CliRunner
from cum import config, cum
from shutil import copyfile
import os
import tempfile
import unittest


class CumTest(unittest.TestCase):
    """Base class for all cum test cases."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.batoto_password = os.environ.get('BATOTO_PASSWORD', None)
        self.batoto_username = os.environ.get('BATOTO_USERNAME', None)
        self.madokami_password = os.environ.get('MADOKAMI_PASSWORD', None)
        self.madokami_username = os.environ.get('MADOKAMI_USERNAME', None)

    def copy_broken_database(self):
        """Copies a pre-defined broken database into the current directory."""
        test_directory = os.path.dirname(os.path.realpath(__file__))
        broken_db_path = os.path.join(test_directory, 'broken_database.db')
        target_db_path = os.path.join(self.directory.name, 'cum.db')
        copyfile(broken_db_path, target_db_path)

    @property
    def no_batoto_login(self):
        return not (self.batoto_username and self.batoto_password)

    @property
    def no_madokami_login(self):
        return not (self.madokami_username and self.madokami_password)

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        config.initialize(self.directory.name)
        config.get().download_directory = self.directory.name
        config.get().batoto.password = self.batoto_password
        config.get().batoto.username = self.batoto_username
        config.get().madokami.password = self.madokami_password
        config.get().madokami.username = self.madokami_username
        config.get().write()
        self.runner = CliRunner()


class CumCLITest(CumTest):
    def setUp(self):
        super().setUp()
        self.runner = CliRunner()
        global scrapers
        from cum import db, scrapers
        self.db = db
        self.scrapers = scrapers
        self.db.initialize()

    def tearDown(self):
        self.directory.cleanup()

    def create_mock_chapter(self, alias='', chapter='', directory=None,
                            groups=[], name='', title=None, url=''):
        kwargs = {'alias': alias, 'chapter': chapter, 'directory': directory,
                  'groups': groups, 'name': name, 'title': title, 'url': url}
        chapter = unittest.mock.MagicMock(**kwargs)

        def save(*args, **kwargs):
            return scrapers.base.BaseChapter.save(chapter, *args, **kwargs)
        chapter.save = save
        return chapter

    def create_mock_series(self, alias='', directory=None, name='', url=''):
        """Creates an unit testing mock object that has a lot of the same
        functionality as regular series for testing purposes.
        """
        kwargs = {'alias': alias, 'directory': directory, 'url': url}
        series = unittest.mock.MagicMock(**kwargs)
        series.chapters = []

        def follow(*args, **kwargs):
            return scrapers.base.BaseSeries.follow(series, *args, **kwargs)
        series.follow = follow
        series.name = name
        return series

    def invoke(self, *arguments, **kwargs):
        """Alias for the CliRunner invoke using default arguments needed for testing.
        """
        default_args = ['--cum-directory', self.directory.name]
        args = default_args + list(arguments)
        return self.runner.invoke(cum.cli, args, **kwargs)


def skipIfNoBatotoLogin(test):
    def wrapper(self, *args, **kwargs):
        if getattr(self, 'no_batoto_login'):
            raise unittest.SkipTest('No Batoto login')
        else:
            return test(self, *args, **kwargs)
    return wrapper


def skipIfNoMadokamiLogin(test):
    def wrapper(self, *args, **kwargs):
        if getattr(self, 'no_madokami_login'):
            raise unittest.SkipTest('No Madokami login')
        else:
            return test(self, *args, **kwargs)
    return wrapper
