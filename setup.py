from setuptools import find_packages, setup

setup(
    name='cum',
    version='0.2.1',
    packages=find_packages(),
    py_modules=['cum'],
    install_requires=[
        'beautifulsoup4',
        'Click',
        'natsort',
        'requests',
        'SQLAlchemy'
    ],
    entry_points='''
        [console_scripts]
        cum=cum.cum:cli
    ''',
)
