# BOS-auto

## Entire Setup

1. Install dependencies:

    pip3 install peerplays bos-incidents bookiesports bos-sync

2. Checkout bos-auto

    git checkout https://github.com/pbsa/bos-auto
    cd bos-auto

3. Install dependencies

    pip3 install -r requirements.txt

4. Install databases

    * `mongodb` - interaction between BOS-auto and MINT
    * `redis` - worker queue

5. Setup your python-peerplays wallet

    peerplays addkey
    # provide active private key for the witness

6. Modify configuration

  1. Rename `config-example.yaml` as `config.yaml`
  2. Modify `config.yaml`

7. Start the end point

    cd bos-auto
    python3 cli.py api      [--help for more information]

8. Start worker

    cd bos-auto
    python3 cli.py worker   [--help for more information]


## Configuration


## Requirements

* A Redis database
* A MongoDB database
* python3 deployment

## Executation

    $ python3 cli.py worker &    # Execute worker
    $ python3 cli.py api         # Start web endpoint

## Notifications

### Telegram

https://github.com/sashgorokhov/python-telegram-handler
