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
    forum_url = 'https://bato.to/forums/index.php'
    login_query = {'app': 'core', 'module': 'global',
                   'section': 'login', 'do': 'process'}

    def __init__(self, config, dict):
        self._config = config
        self.cookie = dict.get('cookie', None)
        self.member_id = dict.get('member_id', None)
        self.pass_hash = dict.get('pass_hash', None)
        self.password = dict.get('password', None)
        self.username = dict.get('username', None)

    def login(self):
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
        self.cookie = r.cookies['session_id']
        self.member_id = r.cookies['member_id']
        self.pass_hash = r.cookies['pass_hash']
        self._config.write()

    @property
    def login_cookies(self):
        if not (self.cookie and self.member_id and self.pass_hash):
            self.login()
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

config = BaseConfig()
