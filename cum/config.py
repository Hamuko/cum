from cum import exceptions
import threading
import click
import json
import os
import re
import requests
import sys


class BaseConfig(object):
    def __init__(self):
        self.load()

    def __setattr__(self, name, value):
        """Ensures that changes made after loading with default values
        are written back to disk.
        """
        if hasattr(self, 'persistent_config'):
            self.persistent_config[name] = value
        object.__setattr__(self, name, value)

    @property
    def default_download_directory(self):
        """Returns a platform-specific download directory to use if no download
        directory is specified by the user.
        """
        if sys.platform in ['cygwin', 'win32']:
            return os.path.join(os.environ['USERPROFILE'], 'Downloads')
        else:
            return os.environ['HOME']

    def load(self):
        try:
            f = open(config_path)
        except FileNotFoundError:
            j = {}
        else:
            try:
                j = json.load(f)
            except ValueError as e:
                f.seek(0, 0)
                cfargs = {}
                if hasattr(json.decoder, 'JSONDecodeError'):
                    cfargs = {'config': f.read(),
                              'cursor': (e.lineno, e.colno),
                              'message': 'Error reading config: {}'
                                         .format(e.msg)}
                else:
                    # Remove this hack when we drop Python 3.4 support
                    msg, pos = str(e).split(':')
                    m = re.match(r'\s*line (\d+) column (\d+).*', pos)
                    cur = (int(m.group(1)), int(m.group(2)))
                    cfargs = {'config': f.read(),
                              'cursor': cur,
                              'message': 'Error reading config: {}'
                                         .format(msg)}
                raise exceptions.ConfigError(**cfargs)
            finally:
                f.close()

        self.batoto = BatotoConfig(self, j.get('batoto', {}))
        self.cbz = j.get('cbz', False)
        self.compact_new = j.get('compact_new', False)
        self.download_directory = j.get('download_directory',
                                        self.default_download_directory)
        self.download_threads = j.get('download_threads', 4)
        self.html_parser = j.get('html_parser', 'html.parser')
        self.madokami = MadokamiConfig(self, j.get('madokami', {}))
        self.relative_latest = j.get('relative_latest', False)

        self.persistent_config = j

    def serialize(self):
        """Returns the current persistent configuration as a dictionary. All
        private configuration values starting with an underscore are removed
        from the configuration.
        """
        configuration = dict(self.persistent_config)
        configuration['batoto'] = dict(self.batoto.__dict__)
        configuration['madokami'] = dict(self.madokami.__dict__)
        configuration_keys = list(configuration.keys())
        while True:
            if not configuration_keys:
                break

            key = configuration_keys.pop(0)
            key_levels = key.split('.')
            dictionary = None
            value = configuration[key_levels[0]]
            for level in key_levels[1:]:
                dictionary = value
                value = value[level]

            if key_levels[-1].startswith('_'):
                del dictionary[key_levels[-1]]
                continue
            if isinstance(value, dict):
                dict_keys = ['.'.join([key, x]) for x in value]
                configuration_keys += dict_keys
        return configuration

    def write(self):
        if hasattr(self, 'persistent_config'):
            configuration = self.serialize()

            with open(config_path, 'w') as file:
                json.dump(configuration, file, sort_keys=True, indent=2)


class BatotoConfig(object):
    forum_url = 'https://bato.to/forums/index.php'
    login_query = {'app': 'core', 'module': 'global',
                   'section': 'login', 'do': 'process'}

    def __init__(self, config, dict):
        self._config = config
        self._lock = threading.Lock()
        self._login_attempts = 0
        self.cookie = dict.get('cookie', None)
        self.member_id = dict.get('member_id', None)
        self.pass_hash = dict.get('pass_hash', None)
        self.password = dict.get('password', None)
        self.username = dict.get('username', None)

    def login(self):
        self._login_attempts += 1
        if self._login_attempts > 1:
            raise exceptions.LoginError('Batoto login error')
        if not self.username:
            username = click.prompt('Batoto username')
        else:
            username = self.username
        if not self.password:
            password = click.prompt('Batoto password', hide_input=True)
        else:
            password = self.password
        r = requests.get(self.forum_url, params=self.login_query)
        auth_key = re.search(r"'auth_key' value='(.+)'", r.text).group(1)
        data = {'auth_key': auth_key,
                'referer': 'http://bato.to/',
                'ips_username': username,
                'ips_password': password,
                'rememberMe': 1}
        r = requests.post(self.forum_url, params=self.login_query, data=data)
        try:
            self.cookie = r.cookies['session_id']
            self.member_id = r.cookies['member_id']
            self.pass_hash = r.cookies['pass_hash']
        except KeyError:
            raise exceptions.LoginError('Batoto login error')
        self._config.write()

    @property
    def login_cookies(self):
        self._lock.acquire()
        if not (self.cookie and self.member_id and self.pass_hash):
            self.login()
        self._lock.release()
        return {'session_id': self.cookie,
                'member_id': self.member_id,
                'pass_hash': self.pass_hash}


class MadokamiConfig(object):
    def __init__(self, config, dict):
        self._config = config
        self.password = dict.get('password', None)
        self.username = dict.get('username', None)

    @property
    def login(self):
        """Returns a tuple containing the username and password. Missing values
        will be prompted from the user during runtime.
        """
        if not self.username:
            self.username = click.prompt('Madokami username')
        if not self.password:
            self.password = click.prompt('Madokami password', hide_input=True)
        return (self.username, self.password)


def get():
    """Returns the active config object."""
    return _config


def initialize(directory=None):
    """Initializes the cum directory and config file either with specified
    directory or ~/.cum.
    """
    global _config, config_path, cum_dir
    if directory:
        cum_dir = directory
    elif sys.platform in ['cygwin', 'win32']:
        cum_dir = os.path.join(os.environ['APPDATA'], 'cum')
    else:
        cum_dir = os.path.join(os.environ['HOME'], '.cum')
    if not os.path.exists(cum_dir):
        os.mkdir(cum_dir)
    config_path = os.path.join(cum_dir, 'config.json')
    _config = BaseConfig()
