#!/usr/bin/env python

from setuptools import setup
import sys

__VERSION__ = '0.0.1'

assert sys.version_info[0] == 3, "We require Python > 3"

setup(
    name='bookied',
    version=__VERSION__,
    description=(
        'A daemon to keep the blockchain bookie DApp in sync (i.e., an oracle'
        ' daemon)'
    ),
    long_description=open('README.md').read(),
    download_url='https://github.com/pbsa/bookied/tarball/' + __VERSION__,
    author='Fabian Schuh',
    author_email='Fabian@chainsquad.com',
    maintainer='Fabian Schuh',
    maintainer_email='Fabian@chainsquad.com',
    url='http://pbsa.info',
    keywords=['peerplays', 'bookie'],
    packages=[
        "bookie",
        "bookie_lookup"
    ],
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
    ],
    entry_points={
        'console_scripts': [
            'bookied = bookie.cli:main'
        ],
    },
    install_requires=[
        "peerplays",
        "prettytable",
        "click",
        "pyyaml",
        "colorlog",
        "flask",
        "redis",
        "flask-rq",
        "dateutils",
        "bookiesports",
        # "bookied-scrapers",
    ],
    setup_requires=['pytest-runner'],
    tests_require=['pytest'],
    include_package_data=True,
)
