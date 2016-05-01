from cum import db, config, output
from cum.scrapers import chapter_scrapers, series_scrapers
import click
import datetime
import re


def chapter_by_url(url):
    """Helper function that iterates through the chapter scrapers defined in
    cum.scrapers.__init__ and returns an initialized chapter object when it
    matches the URL regex.
    """
    for Chapter in chapter_scrapers:
        if re.match(Chapter.url_re, url):
            return Chapter.from_url(url)


def list_new():
    """Helper method used in multiple cum commands to print out the new chapter
    details for each series. Has two possible styles for displaying the
    information: compact and normal.
    """
    items = {}
    for chapter in db.Chapter.find_new():
        try:
            items[chapter.alias].append(chapter.chapter)
        except KeyError:
            items[chapter.alias] = [chapter.chapter]
    if not items:
        return

    # Create a sorted list of tuples where the first value of the tuple is the
    # series alias and second is a string containing the new chapters for the
    # series separated by two spaces.
    new = [(x, '  '.join([y for y in items[x]])) for x in sorted(items)]

    if config.get().compact_new:
        print_new_compact(new)
    else:
        print_new_normal(new)


def print_new_compact(items):
    """Prints the new chapter information. E.g.
        joukamachi-no-dandelion 30  31  32  33  34
        minami-ke               153  154  155  156  157
    """
    output.even_columns(items, bold_first_column=True)


def print_new_normal(items):
    """Prints the new chapter information. E.g.
        joukamachi-no-dandelion
        30  31  32  33  34
        minami-ke
        153  154  155  156  157
    """
    width = click.get_terminal_size()[0]
    for series in items:
        click.secho(series[0], bold=True)
        click.echo(click.wrap_text(series[1], width=width))


def series_by_url(url):
    """Helper function that iterates through the series scrapers defined in
    cum.scrapers.__init__ and returns an initialized series object when it
    matches the URL regex.
    """
    for Series in series_scrapers:
        if re.match(Series.url_re, url):
            return Series(url)


def set_ignored(mark_ignored, alias, chapters):
    """Helper function for `cum ignore` and `cum unignore` commands, which will
    either ignore chapters if mark_ignored is True or unignore chapters if
    mark_ignored is False.
    """
    if mark_ignored:
        downloaded = 0
        message_start = 'I'
        method = 'ignore'
    else:
        downloaded = -1
        message_start = 'Uni'
        method = 'mark_new'

    s = db.Series.alias_lookup(alias)
    query = (db.session.query(db.Chapter)
                       .filter(db.Chapter.series == s,
                               db.Chapter.downloaded == downloaded))
    if len(chapters) == 1 and chapters[0].lower() == 'all':
        click.echo('{}gnoring {} chapters for {}'
                   .format(message_start, len(s.chapters), s.name))
        click.confirm('Do you want to continue',
                      prompt_suffix='? ', abort=True)
    else:
        query = query.filter(db.Chapter.chapter.in_(chapters))

    chapters = [x.to_object() for x in query.all()]
    for chapter in chapters:
        function = getattr(chapter, method)
        function()
    if len(chapters) == 1:
        output.chapter('{}gnored chapter {} for {}'
                       .format(message_start, chapters[0].chapter, s.name))
    else:
        output.series('{}gnored {} chapters for {}'
                      .format(message_start, len(chapters), s.name))


def time_to_relative(time):
    """Converts a DateTime object into a string containing the relative time of
    the DateTime, e.g. "3 minutes ago".
    """
    delta = datetime.datetime.now() - time
    if delta.days >= 30:
        value = delta.days // 30
        unit = 'months'
    elif delta.days > 0:
        value = delta.days
        unit = 'days'
    elif delta.seconds >= 60 * 60:
        value = delta.seconds // (60 * 60)
        unit = 'hours'
    elif delta.seconds >= 60:
        value = delta.seconds // 60
        unit = 'minutes'
    else:
        value = delta.seconds
        unit = 'seconds'
    if value == 1:
        unit = unit.rstrip('s')
    return '{} {} ago'.format(value, unit)
