#!/usr/bin/env python

from setuptools import setup
import sys

__VERSION__ = '0.0.1'

assert sys.version_info[0] == 3, "We requires Python > 3"

setup(
    name='peerplays-bookie',
    version=__VERSION__,
    description='A library that allows to lookup sports in bookie',
    long_description=open('README.md').read(),
    download_url='https://github.com/pbsa/bookielookup/tarball/' + __VERSION__,
    author='Fabian Schuh',
    author_email='Fabian@chainsquad.com',
    maintainer='Fabian Schuh',
    maintainer_email='Fabian@chainsquad.com',
    url='http://pbsa.info',
    keywords=['peerplays', 'bookie'],
    packages=["bookie", "witnesslookup"],
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
    ],
    entry_points={
        'console_scripts': [
            'bookie = bookie.cli:main'
        ],
    },
    install_requires=[
        "peerplays",
        "prettytable",
        "click",
        "pyyaml",
        "colorlog",
    ],
    setup_requires=['pytest-runner'],
    tests_require=['pytest'],
    include_package_data=True,
)
