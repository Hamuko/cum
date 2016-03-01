# cum

[![Build Status](https://travis-ci.org/Hamuko/cum.svg?branch=master)](https://travis-ci.org/Hamuko/cum)
[![codecov.io](https://codecov.io/github/Hamuko/cum/coverage.svg?branch=master)](https://codecov.io/github/Hamuko/cum?branch=master)

comic updater, mangafied

## Description
cum (comic updater, mangafied) is a tool designed for automated manga downloads from various online manga aggregate sites. Currently, the code is young and messy, so you should expect there to be issues and missing functionality. Please open up an issue on the tracker or submit a pull request to help out.

## Installation

You can install cum on your system by executing `python setup.py install`. You can also execute the `cum.py` file directly, but it's not nearly as nice to use as the installed version. Please note that cum only supports Python 3.3+ at the moment.

Users of Arch Linux can install stable versions [from the AUR](https://aur.archlinux.org/packages/cum/).

## Usage

To print out a list of available commands, use `cum --help`. For help with a particular command, use `cum COMMAND --help`.

### Config

Config is stored at `~/.cum/config.json` and overwrites the following default values. Cum will not write login information supplied by the user at run-time back to the config file, but will store session cookies if any exist.

```javascript
{
  "batoto": {
    "cookie": "",  // Used to login to Batoto.
    "member_id": "",  // Used to login to Batoto.
    "pass_hash": "",  // Used to login to Batoto.
    "password": "",  // Password to use with Batoto logins.
    "username": ""  // Username to use with Batoto logins.
  }
  "cbz": false,  // If true, the archive extension will be .cbz instead of .zip.
  "compact_new": true,  // Uses compact listing mode for `cum new`.
  "download_directory": "~",  // Directory where manga is downloaded.
  "download_threads": 4,  // Maximum number of concurrent downloads.
  "html_parser": "html.parser",  // HTML parser used by cum.
  "madokami": {
    "password": "" // Password to use with Madokami
    "username": "", // Username to use with Madokami.
  }
}
```

### Commands

```
alias      Assign a new alias to series.
chapters   List all chapters for a manga series.
download   Download all available chapters.
follow     Follow a series.
  --directory TEXT  Directory which download the series chapters into.
  --download        Downloads the chapters for the added follows.
  --ignore          Ignores the chapters for the added follows.
follows    List all follows.
get        Download chapters by URL or by alias:chapter.
  --directory TEXT  Directory which download chapters into.
ignore     Ignore chapters for a series.
new        List all new chapters.
open       Open the series URL in a browser.
repair-db  Runs an automated database repair.
unfollow   Unfollow manga.
unignore   Unignore chapters for a series.
update     Gather new chapters from followed series.
```

### Examples

```bash
# Update the database with possible new chapters for followed series.
$ cum update

# List all new, non-ignored chapters.
$ cum new

# Add a follow for a manga series.
$ cum follow http://bato.to/comic/_/comics/gakkou-gurashi-r9554

# Print out the chapter list for the added series.
$ cum chapters gakkou-gurashi

# Ignore the first three chapters for the added series.
$ cum ignore gakkou-gurashi 2 3 1

# Change the alias for the added series.
$ cum alias gakkou-gurashi school-live

# Download all new, non-ignored chapters for the added series using the new alias.
$ cum download school-live
```

## Supported sites

See the [Supported sites](../../wiki/Supported-sites) wiki page for details.

## Dependencies

* [alembic](https://pypi.python.org/pypi/alembic)
* [beautifulsoup4](https://pypi.python.org/pypi/beautifulsoup4)
* [click](https://pypi.python.org/pypi/click/4.0)
* [natsort](https://pypi.python.org/pypi/natsort/4.0.3)
* [requests](https://pypi.python.org/pypi/requests/2.7.0)
* [SQLAlchemy](https://pypi.python.org/pypi/SQLAlchemy/1.0.6)

## Community

There is an (inactive) IRC channel for cum: `#cu` on `irc.rizon.net`.

## Design choices

* File output format is partially based on Daiz's [Manga Naming Scheme](https://gist.github.com/Daiz/bb8424cfedd0f05b7386).
  * The full format would be a nightmare to get working with the sparse information available on scraper sites.
* Code styling is based on [Pocoo Style Guide](http://www.pocoo.org/internal/styleguide/) with 79 character line limit.
