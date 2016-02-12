from abc import ABCMeta, abstractmethod
from concurrent.futures import ThreadPoolExecutor
from cum import db, output
from cum.config import config
from functools import partial
from mimetypes import guess_extension
from re import match, sub
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import NoResultFound
from tempfile import NamedTemporaryFile
import click
import os
import requests
import zipfile


download_pool = ThreadPoolExecutor(config.download_threads)


class BaseSeries(metaclass=ABCMeta):
    """Class that is used to represent an individual series on a site."""

    @abstractmethod
    def __init__(self, url):
        pass

    @property
    def alias(self):
        """Returns an alias version of the series name, which only allows a
        certain command-line friendly set of characters.
        """
        allowed_re = r'[A-Za-z0-9\-\s]'

        # Take the series name, lowercase it, replace all spaces with dashes
        # and then replaces all repeating dashes with a single dash.
        name = sub('-+', '-', self.name.lower().replace(' ', '-'))

        # Return the string where all characters are matched to allowed_re.
        return ''.join(c for c in name if match(allowed_re, c))

    def follow(self, ignore=False):
        """Adds the series details to database and all current chapters."""
        output.series('Adding follow for {s.name} ({s.alias})'.format(s=self))

        try:
            s = db.session.query(db.Series).filter_by(url=self.url).one()
        except NoResultFound:
            s = db.Series(self)
            db.session.add(s)
            db.session.commit()
        else:
            if s.following:
                output.warning('You are already following this series')
            else:
                s.following = True
                db.session.commit()

        for chapter in self.chapters:
            chapter.save(s, ignore=ignore)

    @abstractmethod
    def get_chapters(self):
        """Returns a list of objects that represent all of the series' chapters
        and are based on the Chapter class.
        """
        pass

    @property
    @abstractmethod
    def name(self):
        """Returns a string containing the title of the series."""
        pass

    def update(self):
        """Iterates through the currently available chapters and saves them in
        the database.
        """
        s = db.session.query(db.Series).filter_by(url=self.url).one()

        for chapter in self.chapters:
            chapter.save(s)


class BaseChapter(metaclass=ABCMeta):
    """Class that is used to represent an individual download on a site."""

    @abstractmethod
    def __init__(self, name=None, alias=None, chapter=None,
                 url=None, groups=[], title=None):
        pass

    def available(self):
        """Checks if chapter URL returns HTTP 404 or not, and returns a boolean
        value based on it. Broken links are pruned from the database.

        Some sites might not return HTTP 404 on missing chapters and require
        custom version of this method to work.
        """
        r = requests.head(self.url)
        if r.status_code == 404:
            return False
        else:
            return True

    def create_zip(self, files):
        """Takes a list of named temporary files, makes a ZIP out of them and
        closes the temporary files, deleting them. Files inside the .zip are
        organized based on the list order with rolling numbering padded to six
        digits and with the prefix 'image'.
        """
        with zipfile.ZipFile(self.filename, 'w') as z:
            for num, f in enumerate(files):
                root, ext = os.path.splitext(f.name)
                z.write(f.name, 'img{num:0>6}{ext}'.format(num=num, ext=ext))
                f.close()

    def db_remove(self):
        """Removes the chapter from the database."""
        c = db.session.query(db.Chapter).filter_by(url=self.url).one()
        db.session.delete(c)
        try:
            db.session.commit()
        except:
            db.session.rollback()

    @abstractmethod
    def download(self):
        """Method that downloads the chapter and saves it in the appropriate
        directory as one archive file.
        """
        pass

    @property
    def filename(self):
        keepcharacters = [' ', '.', '-', '_', '[', ']', '/', "'"]

        name = self.name.replace('/', '')

        # Individually numbered chapter or a chapter range (e.g. '35',
        # '001-007').
        if match(r'[0-9\-]*$', self.chapter):
            chapter = ('c' +
                       '-'.join(x.zfill(3) for x in self.chapter.split('-')))
        # Individually numbered chapter with letter following the number
        # (e.g. '35v2', '9a').
        elif match(r'[0-9]*[A-Za-z][0-9]*?$', self.chapter):
            number = match(r'([0-9]*)[A-Za-z]', self.chapter).group(1)
            chapter = 'c{:0>3}'.format(number)
        # Individually numbered chapter with decimal (e.g. '1.5').
        elif match(r'[0-9]*\.[0-9]*$', self.chapter):
            number, decimal = self.chapter.split('.')
            chapter = 'c{:0>3} x{}'.format(number, decimal)
        # Failing all else, e.g. 'Special'. Becomes 'c000 [Special]'.
        else:
            chapter = 'c000 [{}]'.format(self.chapter)

        if self.groups:
            group = ''.join('[{}]'.format(g) for g in self.groups)
        else:
            group = '[Unknown]'

        if config.cbz:
            ext = 'cbz'
        else:
            ext = 'zip'

        # Expand ~ to user directory if it's the config.
        download_dir = os.path.expanduser(config.download_directory)

        # Format the filename somewhat based on Daiz's manga naming scheme.
        # Remove any '/' characters to prevent the name of the manga splitting
        # the files into an unwanted sub-directory.
        filename = '{} - {} {}.{}'.format(name, chapter, group,
                                          ext).replace('/', '')

        # Join the path parts and sanitize any unwanted characters that might
        # cause issues with filesystems. Remove repeating whitespaces.
        target = os.path.join(download_dir, name, filename)
        target = ''.join([c for c in target if c.isalpha()
                          or c.isdigit() or c in keepcharacters]).rstrip()
        target = sub(' +', ' ', target)

        # Make sure that the path exists before the filename is returned.
        directory = os.path.dirname(target)
        if not os.path.exists(directory):
            os.makedirs(directory)

        return target

    @staticmethod
    @abstractmethod
    def from_url(url):
        """Method to initialize a Chapter object from the chapter URL."""
        pass

    def get(self, use_db=True):
        """Downloads the chapter if it is available.

        Optionally does not attempt to remove the chapter from the database or
        mark the chapter as downloaded if `db_remove` is set to False.
        """
        if self.available():
            self.download()
            if use_db:
                self.mark_downloaded()
        elif use_db:
            output.warning('Removing {} {}: missing from remote'
                           .format(self.name, self.chapter))
            self.db_remove()

    def ignore(self):
        """Fetches the chapter from the database and marks it ignored."""
        c = db.session.query(db.Chapter).filter_by(url=self.url).one()
        c.downloaded = -1
        db.session.commit()

    def mark_downloaded(self):
        """Fetches the chapter from the database and marks it downloaded."""
        c = db.session.query(db.Chapter).filter_by(url=self.url).one()
        c.downloaded = 1
        db.session.commit()

    def mark_new(self):
        """Fetches the chapter from the database and marks it new."""
        c = db.session.query(db.Chapter).filter_by(url=self.url).one()
        c.downloaded = 0
        db.session.commit()

    @staticmethod
    def page_download_task(page_num, r):
        """Saves the response body of a single request, returning the file
        handle and the passed through number of the page to allow for non-
        sequential downloads in parallel.
        """
        ext = guess_extension(r.headers.get('content-type'))
        f = NamedTemporaryFile(suffix=ext)
        for chunk in r.iter_content(chunk_size=4096):
            if chunk:
                f.write(chunk)
        f.flush()
        return((page_num, f))

    @staticmethod
    def page_download_finish(bar, files, fs):
        """Callback functions for page_download_task futures, assigning the
        resulting filehandles to the right index in the array and updating
        the progress bar.
        """
        index, f = fs.result()
        files[index] = f
        bar.update(1)

    def progress_bar(self, arg):
        """Returns a pre-configured Click progress bar to use with downloads.
        If chapter uses separate page downloads, page download progress is
        shown (e.g. '7/20').
        """
        if self.uses_pages:
            iterable = arg
            length = None
        else:
            iterable = None
            length = arg

        click.echo('{c.alias} {c.chapter}'.format(c=self))
        return click.progressbar(iterable=iterable, length=length,
                                 fill_char='>', empty_char=' ',
                                 show_pos=self.uses_pages, show_percent=True)

    def save(self, series, ignore=False):
        """Save a chapter to database."""
        try:
            c = db.Chapter(self, series)
        except IntegrityError:
            db.session.rollback()
        else:
            if ignore:
                c.downloaded = -1
            db.session.add(c)
            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()
