from setuptools import find_packages, setup
import sys


class PythonVersionException(Exception):
    __module__ = Exception.__module__

    def __init__(self, message):
        self.message = message

    def __str__(self):
        return repr(self.message)

if sys.version_info[0] < 3:
    raise PythonVersionException('Python 3.x required.')

setup(
    name='cum',
    version='0.4',
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
