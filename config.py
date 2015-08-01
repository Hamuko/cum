import click
import json
import os

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

        self.cbz = j.get('cbz', False)
        self.download_directory = j.get('download_directory', home_dir)
        self.madokami = MadokamiConfig(j.get('madokami', {}))

    def write(self):
        config = self.__dict__
        config['madokami'] = self.madokami.__dict__

        with open(config_path, 'w') as file:
            json.dump(config, file, indent=2)


class MadokamiConfig(object):
    def __init__(self, dict):
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
