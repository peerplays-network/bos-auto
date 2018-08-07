import os
import yaml


def loadConfig(config_file="config.yaml"):
    """ Load the configuration from a YAML file
    """
    config = dict()
    default_file = os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        "config-default.yaml"
    )
    with open(default_file) as fid:
        config.update(yaml.load(fid))

    # Load wallet passphrase from config
    if os.path.isfile(config_file):
        with open(config_file, "r") as fid:
            config.update(yaml.load(fid))

    return config
