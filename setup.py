from setuptools import find_packages, setup
import sys
import os
import subprocess


class PythonVersionException(Exception):
    __module__ = Exception.__module__

    def __init__(self, message):
        self.message = message

    def __str__(self):
        return repr(self.message)


def get_version():
    """Returns a version that will either result as "0.1" style string if the
    git commit is tagged or as "git-ebe0338" otherwise. If there is no
    directory named ".git'", the function will instead return False.
    """
    COMMAND_DESCRIBE = ['git', 'describe', '--tags', '--exact-match']
    COMMAND_REV_PARSE = ['git', 'rev-parse', '--short', 'HEAD']
    KWARGS = {
        'cwd': script_path,
        'stdout': subprocess.PIPE,
        'stderr': subprocess.PIPE
    }
    version_is_commit = False
    if os.path.isdir('.git'):
        process = subprocess.Popen(COMMAND_DESCRIBE, **KWARGS)
        process.wait()
        if process.returncode != 0:
            version_is_commit = True
            process = subprocess.Popen(COMMAND_REV_PARSE, **KWARGS)
            process.wait()
        version = process.communicate()[0].decode("utf-8").strip()
        if version_is_commit:
            version = '-'.join(['git', version])
        else:
            version = version[1:]
        return version
    else:
        return False


def write_version_file():
    version_file_path = os.path.join(script_path, 'cum/version.py')
    with open(version_file_path, 'r') as file:
        lines = file.readlines()
        lines[0] = "__version__ = '{}'\n".format(version)
    with open(version_file_path, 'w') as file:
        for line in lines:
            file.write(line)


if sys.version_info[0] < 3:
    raise PythonVersionException('Python 3.x required.')


script_path = os.path.dirname(os.path.realpath(__file__))
git_path = os.path.join(script_path, '.git')

version = get_version()
if version:
    write_version_file()

from cum.version import __version__

setup(
    name='cum',
    version=__version__,
    description='comic updater, mangafied',
    url='https://github.com/Hamuko/cum',
    license='Apache2',
    packages=find_packages(),
    install_requires=[
        'alembic',
        'beautifulsoup4',
        'Click',
        'natsort',
        'requests',
        'SQLAlchemy'
    ],
    entry_points={
        'console_scripts': ['cum=cum.cum:cli'],
    }
)
