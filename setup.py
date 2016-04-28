from setuptools import find_packages, setup
import os
import re
import subprocess
import sys


script_path = os.path.dirname(os.path.realpath(__file__))
git_path = os.path.join(script_path, '.git')
re_version = r'v([0-9\.]*-?[0-9]*)?'
COMMAND_DESCRIBE = ['git', 'describe', '--tags', '--exact-match']
COMMAND_DESCRIBE_VERSION = ['git', 'describe', '--tags']
COMMAND_REV_PARSE = ['git', 'rev-parse', '--short', 'HEAD']
SUBPROCESS_KWARGS = {
    'cwd': script_path,
    'stdout': subprocess.PIPE,
    'stderr': subprocess.PIPE
}


class PythonVersionException(Exception):
    __module__ = Exception.__module__

    def __init__(self, message):
        self.message = message

    def __str__(self):
        return repr(self.message)


def get_setup_version():
    """Return a version string that can be used with the setup method. Includes
    additional commits since the last tagged commit.
    """
    if os.path.isdir('.git'):
        process = subprocess.Popen(COMMAND_DESCRIBE_VERSION,
                                   **SUBPROCESS_KWARGS)
        process.wait()
        version = process.communicate()[0].decode("utf-8").strip()
        return re.match(re_version, version).group(1)
    else:
        from cum.version import __version__
        return __version__


def get_version():
    """Returns a version that will either result as "0.1" style string if the
    git commit is tagged or as "git-ebe0338" otherwise. If there is no
    directory named ".git'", the function will instead return False.
    """
    version_is_commit = False
    if os.path.isdir('.git'):
        process = subprocess.Popen(COMMAND_DESCRIBE, **SUBPROCESS_KWARGS)
        process.wait()
        if process.returncode != 0:
            version_is_commit = True
            process = subprocess.Popen(COMMAND_REV_PARSE, **SUBPROCESS_KWARGS)
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
    """Writes a version.py file containing the current version. Only replaces
    the first line of the file so that the rest of the variables and functions
    can still be used normally.
    """
    version_file_path = os.path.join(script_path, 'cum/version.py')
    with open(version_file_path, 'r') as file:
        lines = file.readlines()
        lines[0] = "__version__ = '{}'\n".format(version)
    with open(version_file_path, 'w') as file:
        for line in lines:
            file.write(line)


if sys.version_info[0] < 3:
    raise PythonVersionException('Python 3.x required.')


version = get_version()
if version:
    write_version_file()

setup(
    name='cum',
    version=get_setup_version(),
    description='comic updater, mangafied',
    url='https://github.com/Hamuko/cum',
    author='Hamuko',
    author_email='hamuko@burakku.com',
    license='Apache2',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Console',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Topic :: Internet :: WWW/HTTP'
    ],
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
