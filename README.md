# Bookied Automation API

## Installation

    $ pip3 install .

## Configuration

1. Rename `config-example.yaml` as `config.yaml`
2. Modify `config.yaml`

## Requirements

* A Redis database

## Executation

    $ python3 cli.py worker &    # Execute worker
    $ python3 cli.py api         # Start web endpoint

## Test

    $ python3 web_t.py
