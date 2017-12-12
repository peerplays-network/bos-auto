import os
import yaml

config_file = "config.yaml"

# Load wallet passphrase from config
if not os.path.isfile(config_file):
    raise Exception("No '{}' file found".format(config_file))

with open(config_file, "r") as fid:
    config = yaml.load(fid)
