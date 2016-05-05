#!/usr/bin/env python3
from cum import config, exceptions, output, version
from functools import wraps
import click
import concurrent.futures


class CumGroup(click.Group):
    def command(self, check_db=True, *args, **kwargs):
        def decorator(f):
            @wraps(f)
            def wrapper(*args, **kwargs):
                if check_db:
                    db.test_database()
                return f(*args, **kwargs)
            return super(CumGroup, self).command(*args, **kwargs)(wrapper)
        return decorator


def edit_defaults():
    """Edits the Click command default values after initializing the config."""
    latest_command = cli.get_command(cli, 'latest')
    for param in latest_command.params:
        if param.human_readable_name == 'relative':
            param.default = config.get().relative_latest


@click.command(cls=CumGroup)
@click.option('--cum-directory',
              help='Directory used by cum to store application files.')
@click.version_option(version=version.__version__,
                      message=version.version_string())
def cli(cum_directory=None):
    global db, output, sanity, utility
    config.initialize(directory=cum_directory)
    from cum import db, output, sanity, utility
    db.initialize()
    edit_defaults()


@cli.command()
@click.argument('alias')
@click.argument('new_alias')
def alias(alias, new_alias):
    """Assign a new alias to series."""
    s = db.Series.alias_lookup(alias)
    s.alias = new_alias
    try:
        db.session.commit()
    except:
        db.session.rollback()
    else:
        output.chapter('Changing alias "{}" to "{}"'.format(alias, new_alias))


@cli.command()
@click.argument('alias')
def chapters(alias):
    """List all chapters for a manga series.

    Chapter listing will contain the flag value for the chapter ('n' for new,
    'i' for ignored and blank for downloaded), the chapter identifier ("chapter
    number") and the possible chapter title and group.
    """
    s = db.Series.alias_lookup(alias)
    if s.chapters:
        click.secho('f  chapter  title [group]', bold=True)
        for chapter in s.ordered_chapters:
            name_len = click.get_terminal_size()[0] - 11
            name = '{} {}'.format(chapter.title, chapter.group_tag)[:name_len]
            row = '{}  {:>7}  {}'.format(chapter.status, chapter.chapter, name)
            if row[0] == 'n':
                style = {'fg': 'white', 'bold': True}
            elif row[0] == ' ':
                style = {'bold': True}
            else:
                style = {}
            click.secho(row, **style)


@cli.command(name='config')
@click.argument('mode')
@click.argument('setting', required=False)
@click.argument('value', required=False)
def config_command(mode, setting, value):
    """Get or set configuration options.

    Mode can be either "get" or "set", depending on whether you want to read or
    write configuration values. If mode is "get", you can specify a setting to
    read that particular setting or omit it to list out all the settings. If
    mode is "set", you must specify the setting to change and assign it a new
    value.
    """
    if mode == 'get':
        if setting:
            parameters = setting.split('.')
            value = config.get()
            for parameter in parameters:
                try:
                    value = getattr(value, parameter)
                except AttributeError:
                    output.error('Setting not found')
                    exit(1)
            output.configuration({setting: value})
        else:
            configuration = config.get().serialize()
            output.configuration(configuration)
    elif mode == 'set':
        if setting is None:
            output.error('You must specify a setting')
            exit(1)
        if value is None:
            output.error('You must specify a value')
            exit(1)
        parameters = setting.split('.')
        preference = config.get()
        for parameter in parameters[0:-1]:
            try:
                preference = getattr(preference, parameter)
            except AttributeError:
                output.error('Setting not found')
                exit(1)
        try:
            current_value = getattr(preference, parameters[-1])
        except AttributeError:
            output.error('Setting not found')
            exit(1)
        if current_value is not None:
            if isinstance(current_value, bool):
                if value.lower() == 'false' or value == 0:
                    value = False
                else:
                    value = True
            else:
                try:
                    value = type(current_value)(value)
                except ValueError:
                    output.error('Type mismatch: value should be {}'
                                 .format(type(current_value).__name__))
                    exit(1)
        setattr(preference, parameters[-1], value)
        config.get().write()
    else:
        output.error('Mode must be either get or set')
        exit(1)


@cli.command()
@click.argument('aliases', required=False, nargs=-1)
def download(aliases):
    """Download all available chapters.

    If an optional alias is specified, the command will only download new
    chapters for that alias.
    """
    chapters = []
    if not aliases:
        chapters = db.Chapter.find_new()
    for alias in aliases:
        chapters += db.Chapter.find_new(alias=alias)
    output.chapter('Downloading {} chapters'.format(len(chapters)))
    for chapter in chapters:
        try:
            chapter.get()
        except exceptions.LoginError as e:
            output.warning('Could not download {c.alias} {c.chapter}: {e}'
                           .format(c=chapter, e=e.message))
            continue


@cli.command()
@click.argument('urls', required=True, nargs=-1)
@click.option('--directory',
              help='Directory which download the series chapters into.')
@click.option('--download', is_flag=True,
              help='Downloads the chapters for the added follows.')
@click.option('--ignore', is_flag=True,
              help='Ignores the chapters for the added follows.')
def follow(urls, directory, download, ignore):
    """Follow a series."""
    chapters = []
    for url in urls:
        try:
            series = utility.series_by_url(url)
        except exceptions.ScrapingError:
            output.warning('Scraping error ({})'.format(url))
            continue
        except exceptions.LoginError as e:
            output.warning('{} ({})'.format(e.message, url))
            continue
        if not series:
            output.warning('Invalid URL "{}"'.format(url))
            continue
        series.directory = directory
        if ignore:
            series.follow(ignore=True)
            output.chapter('Ignoring {} chapters'.format(len(series.chapters)))
        else:
            series.follow()
            chapters += db.Chapter.find_new(alias=series.alias)

    if download:
        output.chapter('Downloading {} chapters'.format(len(chapters)))
        for chapter in chapters:
            try:
                chapter.get()
            except exceptions.LoginError as e:
                output.warning('Could not download {c.alias} {c.chapter}: {e}'
                               .format(c=chapter, e=e.message))
                continue


@cli.command()
def follows():
    """List all follows.

    Will list all of the active follows in the database as a list of aliases.
    To find out more information on an alias, use the info command.
    """
    query = (db.session.query(db.Series)
             .filter_by(following=True)
             .order_by(db.Series.alias)
             .all())
    output.list([x.alias for x in query])


@cli.command()
@click.argument('input', required=True, nargs=-1)
@click.option('--directory',
              help='Directory which download chapters into.')
def get(input, directory):
    """Download chapters by URL or by alias:chapter.

    The command accepts input as either the chapter of the URL or the
    alias:chapter combination (e.g. 'bakuon:11'), if the chapter is already
    found in the database through a follow. The command will not enter the
    downloads in the database in case of URLs and ignores downloaded status
    in case of alias:chapter, so it can be used to download one-shots that
    don't require follows or for redownloading already downloaded chapters.
    """
    chapter_list = []
    for i in input:
        try:
            series = utility.series_by_url(i)
        except exceptions.ScrapingError:
            output.warning('Scraping error ({})'.format(i))
            continue
        except exceptions.LoginError as e:
            output.warning('{} ({})'.format(e.message, i))
            continue
        if series:
            chapter_list += series.chapters
        try:
            chapter = utility.chapter_by_url(i)
        except exceptions.ScrapingError:
            output.warning('Scraping error ({})'.format(i))
            continue
        except exceptions.LoginError as e:
            output.warning('{} ({})'.format(e.message, i))
            continue
        if chapter:
            chapter_list.append(chapter)
        if not series or chapter:
            try:
                a, c = i.split(':')
            except ValueError:
                output.warning('Invalid selection "{}"'.format(i))
            else:
                chapters = (db.session.query(db.Chapter)
                            .join(db.Series)
                            .filter(db.Series.alias == a,
                                    db.Chapter.chapter == c)
                            .all())
                for chapter in chapters:
                    chapter_list.append(chapter.to_object())
    for chapter in chapter_list:
        chapter.directory = directory
        try:
            chapter.get(use_db=False)
        except exceptions.LoginError as e:
            output.warning('Could not download {c.alias} {c.chapter}: {e}'
                           .format(c=chapter, e=e.message))
            continue


@cli.command()
@click.argument('alias')
@click.argument('chapters', required=True, nargs=-1)
def ignore(alias, chapters):
    """Ignore chapters for a series.

    Enter one or more chapters after the alias to ignore them. Enter the
    chapter identifiers as they are listed when using the chapters command. To
    ignore all of the chapters for a particular series, use the word "all" in
    place of the chapters.
    """
    utility.set_ignored(True, alias, chapters)


@cli.command()
@click.argument('alias', required=False)
@click.option('--relative/--no-relative', default=False,
              help='Uses relative times instead of absolute times.')
def latest(alias, relative):
    """List most recent chapter addition for series."""
    query = (db.session.query(db.Series)
                       .filter_by(following=True)
                       .order_by(db.Series.alias)
                       .all())
    updates = []
    for series in query:
        if series.last_added is None:
            time = 'never'
        elif relative:
            time = utility.time_to_relative(series.last_added)
        else:
            time = series.last_added.strftime('%Y-%m-%d %H:%M')
        updates.append((series.alias, time))
    output.even_columns(updates, separator_width=3)


@cli.command()
def new():
    """List all new chapters."""
    utility.list_new()


@cli.command()
@click.argument('alias')
def open(alias):
    """Open the series URL in a browser."""
    s = db.Series.alias_lookup(alias)
    click.launch(s.url)


@cli.command(check_db=False, name='repair-db')
def repair_db():
    """Runs an automated database repair."""
    sanity_tester = sanity.DatabaseSanity(db.Base, db.engine)
    sanity_tester.test()
    if sanity_tester.errors:
        output.series('Backing up database to cum.db.bak')
        db.backup_database()
        output.series('Running database repair')
        for error in sanity_tester.errors:
            error.fix()


@cli.command()
@click.argument('alias')
def unfollow(alias):
    """Unfollow manga.

    Will mark a series as unfollowed. In order not to lose history of
    downloaded chapters, the series is merely marked as unfollowed in the
    database rather than removed.
    """
    s = db.Series.alias_lookup(alias)
    s.following = False
    db.session.commit()
    output.series('Removing follow for {}'.format(s.name))


@cli.command()
@click.argument('alias')
@click.argument('chapters', required=True, nargs=-1)
def unignore(alias, chapters):
    """Unignore chapters for a series.

    Enter one or more chapters after the alias to mark them as new. Enter the
    chapter identifiers as they are listed when using the chapters command. To
    unignore all of the chapters for a particular series, use the word "all" in
    place of the chapters.
    """
    utility.set_ignored(False, alias, chapters)


@cli.command()
def update():
    """Gather new chapters from followed series."""
    pool = concurrent.futures.ThreadPoolExecutor(config.get().download_threads)
    futures = []
    warnings = []
    aliases = {}
    query = db.session.query(db.Series).filter_by(following=True).all()
    output.series('Updating {} series'.format(len(query)))
    for follow in query:
        fut = pool.submit(utility.series_by_url, follow.url)
        futures.append(fut)
        aliases[fut] = follow.alias
    with click.progressbar(length=len(futures), show_pos=True,
                           fill_char='>', empty_char=' ') as bar:
        for future in concurrent.futures.as_completed(futures):
            try:
                series = future.result()
            except exceptions.ConnectionError:
                warnings.append('Unable to update {} (connection error)'
                                .format(aliases[future]))
            except exceptions.ScrapingError:
                warnings.append('Unable to update {} (scraping error)'
                                .format(aliases[future]))
            except exceptions.LoginError as e:
                warnings.append('Unable to update {} ({})'
                                .format(aliases[future], e.message))
            else:
                series.update()
            bar.update(1)
    for w in warnings:
        output.warning(w)
    utility.list_new()


if __name__ == '__main__':
    cli()
