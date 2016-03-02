import click
from math import ceil


def chapter(msg):
    click.echo(
        click.style('==> ', fg='green') + msg
    )


def configuration(dictionary):
    settings = configuration_flatten(dictionary)
    for setting, value in sorted(settings.items()):
        if value is not None:
            click.echo('{} = {}'.format(setting, value))


def configuration_flatten(dictionary, parent_key=None):
    items = []
    for key, value in dictionary.items():
        if parent_key:
            new_key = '{}.{}'.format(parent_key, key)
        else:
            new_key = key
        if isinstance(value, dict):
            items.extend(configuration_flatten(value, new_key).items())
        else:
            items.append((new_key, value))
    return dict(items)


def error(msg):
    click.echo(
        click.style('==> ', fg='red') + msg
    )


def list(items):
    """Print out a list of items in columns much like `ls` in bash."""
    if items:
        width = click.get_terminal_size()[0]
        longest = len(max(items, key=len))
        columns = int(width // (longest + 0.5))
        rows = ceil(len(items) / columns)

        for row in range(rows):
            line = []
            for column in range(columns):
                i = rows * column + row
                if i >= len(items):
                    continue
                line.append(items[i].ljust(longest))
            click.echo(' '.join(line))


def series(msg):
    click.echo(
        click.style('==> ', fg='blue', bold=True) + msg
    )


def warning(msg):
    click.echo(
        click.style('==> ', fg='yellow', bold=True) + msg
    )
