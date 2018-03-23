#!/usr/bin/env python

from setuptools import setup
import sys

__VERSION__ = '0.0.3'

assert sys.version_info[0] == 3, "We require Python > 3"

setup(
    name='bookied',
    version=__VERSION__,
    description=(
        'A daemon to manage synchronization with the blockchain'
    ),
    long_description=open('README.md').read(),
    download_url='https://github.com/pbsa/bookied/tarball/' + __VERSION__,
    author='Fabian Schuh',
    author_email='Fabian.Schuh@BlockchainProjectsBV.com',
    maintainer='Fabian Schuh',
    maintainer_email='Fabian.Schuh@BlockchainProjectsBV.com',
    url='http://pbsa.info',
    keywords=['peerplays', 'bookied'],
    packages=[
        "bookied",
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
            'bookied = bookied.cli:main'
        ],
    },
    install_requires=[
        "peerplays",
        "prettytable",
        "click",
        "jsonschema",
        "pyyaml",
        "flask",
        "redis",
        "flask-rq",
        "dateutils",
        "bookiesports",
        "bookied_sync",
    ],
    setup_requires=['pytest-runner'],
    tests_require=['pytest'],
    include_package_data=True,
)
