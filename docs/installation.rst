# Entire Setup

## Install dependencies:

```
pip3 install peerplays bos-incidents bookiesports bos-sync
```

## Checkout bos-auto

```
git checkout https://github.com/pbsa/bos-auto
cd bos-auto
```

## Install dependencies

```
pip3 install -r requirements.txt
```

## Install databases

    * `mongodb` - interaction between BOS-auto and MINT
    * `redis` - worker queue

## Setup your python-peerplays wallet

```
peerplays addkey
# provide active private key for the witness
```

## Modify configuration

  1. Rename `config-example.yaml` as `config.yaml`
  2. Modify `config.yaml`

## Start the end point

```
cd bos-auto
python3 cli.py api      [--help for more information]
```

## Start worker

```
cd bos-auto
python3 cli.py worker   [--help for more information]
```
