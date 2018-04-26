# BOS-auto

![](https://img.shields.io/pypi/v/bos-auto.svg?style=for-the-badge)
![](https://img.shields.io/github/downloads/pbsa/bos-auto/total.svg?style=for-the-badge)
![](https://img.shields.io/pypi/pyversions/bos-auto.svg?style=for-the-badge)

[![docs master](https://readthedocs.org/projects/bos-auto/badge/?version=latest)](http://bos-auto.rtfd.io/en/latest/)
[![docs develop](https://readthedocs.org/projects/bos-auto/badge/?version=develop)](http://bos-auto.rtfd.io/en/develop/)


`bos-auto` is one of two services that are required for proper operation of Bookie Oracle Software(BOS). `bos-auto` comes with a worker and an API to receive data from a Data Proxy. The API receives this data, validates it, and
queues it for a worker to perform corresponding tasks. It
further stores these incidents via [`bos-incidents`](https://github.com/PBSA/bos-incidents) to later be able to
display them in the manual intervention(MINT) module [`bos-mint`](https://github.com/PBSA/bos-mint).

## Documentation
For directions on how to install and run `bos-auto` please visit our [documentation page](http://bos-auto.readthedocs.io/en/develop/installation.html).

[![docs master](https://readthedocs.org/projects/bos-auto/badge/?version=latest)](http://bos-auto.rtfd.io/en/latest/)
[![docs develop](https://readthedocs.org/projects/bos-auto/badge/?version=develop)](http://bos-auto.rtfd.io/en/develop/)

## Requirements

* A Redis database
* A MongoDB database
* python3 deployment

## Execution
```bash
$ python3 cli.py worker &    # Execute worker
$ python3 cli.py api         # Start web endpoint
```

