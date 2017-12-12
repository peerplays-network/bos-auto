import os
import yaml


def loadConfig(config_file="config.yaml"):
    config = dict()

    # Load wallet passphrase from config
    if not os.path.isfile(config_file):
        raise Exception("No '{}' file found".format(config_file))

    with open(config_file, "r") as fid:
        config.update(yaml.load(fid))

    return config
