import click
import json
import os
import re
import requests

home_dir = os.environ['HOME']
cum_dir = os.path.join(home_dir, '.cum')
if not os.path.exists(cum_dir):
    os.mkdir(cum_dir)
config_path = os.path.join(cum_dir, 'config.json')


class BaseConfig(object):
    """docstring for Config"""

    def __init__(self):
        self.load()
        self.write()

    def load(self):
        try:
            f = open(config_path)
        except FileNotFoundError:
            j = {}
        else:
            j = json.load(f)
            f.close()

        self.batoto = BatotoConfig(self, j.get('batoto', {}))
        self.cbz = j.get('cbz', False)
        self.compact_new = j.get('compact_new', False)
        self.download_directory = j.get('download_directory', home_dir)
        self.html_parser = j.get('html_parser', 'html.parser')
        self.madokami = MadokamiConfig(self, j.get('madokami', {}))

    def write(self):
        config = dict(self.__dict__)
        config['batoto'] = dict(self.batoto.__dict__)
        config['madokami'] = dict(self.madokami.__dict__)
        del config['batoto']['_config']
        del config['madokami']['_config']

        with open(config_path, 'w') as file:
            json.dump(config, file, sort_keys=True, indent=2)


class BatotoConfig(object):
    def __init__(self, config, dict):
        self._config = config
        self.username = dict.get('username', None)
        self.password = dict.get('username', None)
        self.cookie = dict.get('cookie', None)

    def login(self):
        if not self.username:
            username = click.prompt('Batoto username')
        if not self.password:
            password = click.prompt('Batoto password', hide_input=True)
        url = 'https://bato.to/forums/index.php'
        query = {'app': 'core', 'module': 'global',
                 'section': 'login', 'do': 'process'}
        r = requests.get(url, params=query)
        auth_key = re.search(r"'auth_key' value='(.+)'", r.text).group(1)
        data = {'auth_key': auth_key,
                'referer': 'http://bato.to/',
                'ips_username': username,
                'ips_password': password,
                'rememberMe': 1}
        r = requests.post(url, params=query, data=data)
        self.cookie = r.cookies['session_id']
        self._config.write()

    @property
    def login_cookies(self):
        if not self.cookie:
            self.login()
        return {'session_id': self.cookie}


class MadokamiConfig(object):
    def __init__(self, config, dict):
        self._config = config
        self.username = dict.get('username', None)
        self.password = dict.get('password', None)

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

config = BaseConfig()
