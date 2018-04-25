# BOS-auto

![](https://img.shields.io/pypi/v/bos-auto.svg?style=for-the-badge)
![](https://img.shields.io/github/downloads/pbsa/bos-auto/total.svg?style=for-the-badge)
![](https://img.shields.io/pypi/pyversions/bos-auto.svg?style=for-the-badge)

[![docs master](https://readthedocs.org/projects/bos-auto/badge/?version=latest)](http://bos-auto.rtfd.io/en/latest/)
[![docs develop](https://readthedocs.org/projects/bos-auto/badge/?version=develop)](http://bos-auto.rtfd.io/en/develop/)


`bos-auto` comes with a worker and an API to receive notifications of a
feed data provider. The API receives those messages, validates them, and
queues them for a worker to perform corresponding tasks. Since the
queuing is performed via redis, a redis backend must be present. It
further stores these incidents via `bos-incidents` to later be able to
show them in the manual intervention module `bos-mint`.

## Documentation

## Requirements

* A Redis database
* A MongoDB database
* python3 deployment

## Executation

    $ python3 cli.py worker &    # Execute worker
    $ python3 cli.py api         # Start web endpoint
