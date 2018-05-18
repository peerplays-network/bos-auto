import os
import yaml

#: Default configuration
DEFAULT = """
######################
# Witness endpoint
######################
# Ideally, the witness endpoint runs on localhost somewhere
node: ws://localhost:8090

######################
# PeerPlays network
######################
# This allows you to specify which version of bookiesport to take
# If you connect to Alice (PeerPlays) and try to use network Baxter
# (PeerPlays testnetwork), an exception will be raised!
# To clarify
#
#   * alice: PeerPlays main blockchain
#   * baxter: PeerPlays public testnet blockchain
#   * charlie: PBSA internal development blockchain
#
network: baxter

######################
## Redis configuration
######################
# This allows you to optionally use a redis database that is not on
# localhost.
redis_host:
redis_port:
redis_password:
redis_db:

#####################
# Safe mode (if True)
#####################
# If this is set to true, the entire software suite will behave as
# usualy but not send any transactions to the backend node.
nobroadcast: False

###################
# Wallet passphrase
###################
# Once you added your active private key into local python-peerplays
# database, you have picked a wallet passphrase. Please provide this
# here to allow bos-auto to spin up automatically on powerup.
passphrase: super-secret-wallet-passphrase

##################
# Data Proxy IP Whitelist
##################
# This option allows to define who is allowed to access the web endpoint
# to send messages to. This is a list of IP or hostnames that are
# resovled at the launch time. DNS changes during run time will not
# propagate!
#
#   * 0.0.0.0 - will allow anyone to send messages
#   * dataproxy.example.com - IP address resolved at startup time.
#
api_whitelist:
 - 0.0.0.0
 - localhost

##################
# Proposer account
##################
# Please provide the account name of the witnesse that is *proposing*
# new proposals. This **must** be an active witness account, otherwise,
# other witnesses will not approve it.
#
# Technically, this needs to be the account name of your witness
BOOKIE_PROPOSER: init0

##################
# Approver account
##################
# Provide the account name that approves proposals for witnesses. This
# must be your active witness-account, otherwise it will not affect
# consensus of any given proposal for witnesses.
#
# Technically, this needs to be the account name of your witness
BOOKIE_APPROVER: init0

####################################
# Default mail destination on errors
####################################
# if your server is properly set up, you will receive email
# notifications on errors to this email address
mailto: info@example.com

###########################
# Telegram
###########################
# Notifications via telgram
#
# Please read
#
#   https://github.com/sashgorokhov/python-telegram-handler
#
# for setting up a telegram notification bot.
telegram_token:
#
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
