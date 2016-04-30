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


def even_columns(items, bold_first_column=False, separator_width=1):
    """Prints two columns with the second column padded so that it always
    begins on the same line, regardless of how long the first column is on the
    same line. Takes input as a list of two item tuples.
    """
    first_column_length = len(max([x[0] for x in items], key=len))
    for item in items:
        padding = first_column_length - len(item[0])
        separator = ' ' * separator_width
        first_column = click.style(item[0] + ' ' * padding,
                                   bold=bold_first_column)
        indent = len(item[0]) + padding + separator_width
        line = click.wrap_text(separator.join([first_column, item[1]]),
                               subsequent_indent=' ' * indent,
                               width=click.get_terminal_size()[0])
        click.echo(line)


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
