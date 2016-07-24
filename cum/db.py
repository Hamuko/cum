from cum import config, output, sanity
from math import sqrt
from natsort import humansorted
from shutil import copyfile
from sqlalchemy import (
    Boolean,
    Column,
    create_engine,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Table
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.orm.exc import NoResultFound
from urllib.parse import urlparse
import click
import datetime
import os
import sqlalchemy.engine.url

Base = declarative_base()

group_table = Table(
    'group_association', Base.metadata,
    Column('chapter_id', Integer, ForeignKey('chapters.id')),
    Column('group_id', Integer, ForeignKey('groups.id'))
)


class Series(Base):
    __tablename__ = 'series'

    id = Column(Integer, primary_key=True)

    name = Column(String)
    alias = Column(String, unique=True, nullable=False)
    url = Column(String, unique=True)
    following = Column(Boolean, default=True)
    directory = Column(String)
    last_updated = Column(DateTime)

    chapters = relationship("Chapter", backref="series")

    def __init__(self, series):
        self.name = series.name
        self.alias = series.alias
        self.url = series.url
        self.directory = series.directory

    @staticmethod
    def alias_lookup(alias, unfollowed=False):
        """Returns a DB object for a series by alias name. Prints an error if
        an invalid alias is specified.
        """
        filters = {'alias': alias}
        if not unfollowed:
            filters['following'] = not unfollowed
        try:
            s = session.query(Series).filter_by(**filters).one()
        except NoResultFound:
            output.error('Could not find alias "{}"'.format(alias))
            exit(1)
        else:
            return s

    def check_alias_uniqueness(self):
        """Check if the series alias is unique before initalizing the series
        object. If the alias is not unique, "-X" is appended to the end of the
        alias where the X is the next available integer. However, if the alias
        is not unique and the series with the same alias is unfollowed, the
        unfollowed series gets the new alias.
        """
        alias = self.alias
        changed = False
        count = 1
        while session.query(Series).filter_by(alias=alias).all():
            changed = True
            alias = '{}-{}'.format(self.alias, count)
            count += 1
        if changed:
            series = session.query(Series).filter_by(alias=self.alias).one()
            if not series.following:
                series.alias = alias
                return
        self.alias = alias

    @property
    def last_added(self):
        """Returns the last time a chapter has been added to the series."""
        updates = sorted([x for x in self.chapters if x.added_on is not None],
                         reverse=True, key=lambda x: x.added_on)
        if updates:
            return updates[0].added_on
        else:
            return None

    def mark_as_updated(self):
        """Updates the timestamp for the last update."""
        self.last_updated = datetime.datetime.now()
        session.commit()

    @property
    def needs_update(self):
        """Returns a boolean indicating if the series is in need of an update
        based on the average release interval.
        """
        if not self.last_added:
            return True
        next_update = self.last_added + self.release_interval
        return datetime.datetime.now() >= next_update

    @property
    def ordered_chapters(self):
        return humansorted(self.chapters, key=lambda x: x.chapter)

    @property
    def release_interval(self):
        """Calculates the average second interval for the series chapter
        releases by calculating an average between new release scrapes and
        subtracting the standard deviation from that. Returns the interval as a
        timedelta object.

        Current time is added to release dates to add an interval between the
        last released chapter and current time.

        Since there is a massive number of chapters added right after each
        other when the series is first added, the interval between two chapter
        releases must be greater than 60 seconds to be counter.
        """
        release_dates = [x.added_on for x in self.chapters if x.added_on]
        release_dates.append(datetime.datetime.now())
        release_dates = sorted(release_dates)
        intervals = []
        for i in range(len(release_dates) - 1):
            interval = (release_dates[i+1] - release_dates[i]).total_seconds()
            if interval > 60:
                intervals.append(interval)
        if len(intervals) == 0:
            average_seconds = 0
        elif len(intervals) == 1:
            average_seconds = intervals[0]
        else:
            mean = float(sum(intervals)) / len(intervals)
            devsum = sum((x - mean) ** 2 for x in intervals)
            dev = sqrt(float(devsum) / len(intervals))
            average_seconds = max((mean - dev/2), 0)
        return datetime.timedelta(seconds=average_seconds)


class Chapter(Base):
    __tablename__ = 'chapters'

    id = Column(Integer, primary_key=True)
    series_id = Column(Integer, ForeignKey('series.id'))

    # Downloaded has the value -1 for ignored chapters, 0 for new chapters and
    # 1 for downloaded chapters.
    downloaded = Column(Integer, default=0)
    chapter = Column(String)
    url = Column(String, unique=True)
    title = Column(String)
    added_on = Column(DateTime)
    api_id = Column(String)

    groups = relationship('Group', secondary=group_table, backref='chapters')

    def __init__(self, chapter, series):
        self.series = series
        self.chapter = chapter.chapter
        self.title = chapter.title
        self.url = chapter.url
        self.added_on = datetime.datetime.now()
        self.api_id = getattr(chapter, 'api_id', None)

        self.groups = []
        for group in chapter.groups:
            try:
                g = session.query(Group).filter(Group.name == group).one()
            except NoResultFound:
                g = Group(group)
                session.add(g)
                session.commit()
            self.groups.append(g)

    @staticmethod
    def find_new(alias=None):
        """Return a list of new chapters as Chapter objects and applies human
        sorting to it. Accepts an optional 'alias' argument, which will filter
        the query.
        """
        query = session.query(Chapter).join(Series).filter(Series.following)
        if alias:
            query = query.filter(Series.alias == alias)
        query = query.filter(Chapter.downloaded == 0).all()
        return humansorted([x.to_object() for x in query],
                           key=lambda x: x.chapter)

    @property
    def group_tag(self):
        """Return a joined string of chapter's groups enclosed in brackets."""
        return ''.join(['[{}]'.format(x.name) for x in self.groups])

    @property
    def status(self):
        """Return the chapter's downloaded status as a one character flag."""
        if self.downloaded == 0:
            return 'n'
        elif self.downloaded == -1:
            return 'i'
        else:
            return ' '

    def to_object(self):
        """Turns a database entry into a chapter object for the respective
        site by parsing the URL.
        """
        parse = urlparse(self.url)
        kwargs = {
            'name': self.series.name,
            'alias': self.series.alias,
            'chapter': self.chapter,
            'url': self.url,
            'groups': self.groups,
            'directory': self.series.directory,
            'api_id': self.api_id
        }
        if parse.netloc == 'bato.to':
            from cum.scrapers.batoto import BatotoChapter
            return BatotoChapter(**kwargs)
        elif parse.netloc == 'dynasty-scans.com':
            from cum.scrapers.dynastyscans import DynastyScansChapter
            return DynastyScansChapter(**kwargs)
        elif parse.netloc == 'manga.madokami.al':
            from cum.scrapers.madokami import MadokamiChapter
            return MadokamiChapter(**kwargs)
        elif parse.netloc == 'kobato.hologfx.com':
            from cum.scrapers.dokireader import DokiReaderChapter
            return DokiReaderChapter(**kwargs)
        elif parse.netloc == 'www.yuri-ism.net':
            from cum.scrapers.yuriism import YuriismChapter
            return YuriismChapter(**kwargs)
        elif parse.netloc == 'manga.famatg.com':
            from cum.scrapers.fallenangels import FallenAngelsChapter
            return FallenAngelsChapter(**kwargs)


class Group(Base):
    __tablename__ = 'groups'

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)

    def __init__(self, name):
        self.name = name

    def __str__(self):
        return self.name


def backup_database():
    """Backs up the database file to a file called cum.db.bak."""
    db_path = os.path.join(config.cum_dir, 'cum.db')
    backup_path = os.path.join(config.cum_dir, 'cum.db.bak')
    copyfile(db_path, backup_path)


def initialize():
    global db_path, engine, session
    db_path = os.path.join(config.cum_dir, 'cum.db')
    db_url = sqlalchemy.engine.url.URL('sqlite', database=db_path)
    engine = create_engine(db_url)
    if not os.path.exists(db_path):
        Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()


def test_database():
    """Runs a database sanity test."""
    sanity_tester = sanity.DatabaseSanity(Base, engine)
    sanity_tester.test()
    if sanity_tester.errors:
        for error in sanity_tester.errors:
            err_target, err_msg = str(error).split(' ', 1)
            message = ' '.join([click.style(err_target, bold=True), err_msg])
            output.warning(message)
        output.error('Database has failed sanity check; '
                     'run `cum repair-db` to repair database')
        exit(1)
