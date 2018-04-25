import os
import yaml

#: Default configuration
DEFAULT = """
# (optional) Redis configuration
redis_host:
redis_port:
redis_password:
redis_db:

# Safe mode (if True)
nobroadcast: False

# Wallet passphrase of pypeerplays
passphrase: super-secret-wallet-passphrase

# Default proposer account (should be witness account)
BOOKIE_PROPOSER: init0

# Default approving account
BOOKIE_APPROVER: init0

# Default mail destination on errors
mailto: info@example.com

# Notifications via telgram
telegram_token:
# python3 -m telegram_handler "${telegram_token}"
telegram_chatid:
"""


def loadConfig(config_file="config.yaml"):
    """ Load the configuration from a YAML file
    """
    config = yaml.load(DEFAULT)

    # Load wallet passphrase from config
    if not os.path.isfile(config_file):
        # raise Exception("No '{}' file found".format(config_file))
        config.update(yaml.load(DEFAULT))
    else:
        with open(config_file, "r") as fid:
            config.update(yaml.load(fid))

    return config
