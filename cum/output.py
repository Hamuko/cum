import click
from math import ceil


def chapter(msg):
    click.echo(
        click.style('==> ', fg='green') + msg
    )


def error(msg):
    click.echo(
        click.style('==> ', fg='red') + msg
    )


def list(items):
    """Print out a list of items in columns much like `ls` in bash."""
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
