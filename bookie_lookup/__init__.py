import logging
from colorlog import ColoredFormatter

LOG_LEVEL = logging.DEBUG
LOGFORMAT = ("  %(log_color)s%(levelname)-8s%(reset)s |"
             " %(log_color)s%(message)s%(reset)s")
logging.root.setLevel(LOG_LEVEL)
formatter = ColoredFormatter(LOGFORMAT)
stream = logging.StreamHandler()
stream.setLevel(LOG_LEVEL)
stream.setFormatter(formatter)
log = logging.getLogger(__name__)
log.setLevel(LOG_LEVEL)
log.addHandler(stream)

# logging.basicConfig(level=logging.DEBUG)

UPDATE_PROPOSING_NEW = 1
UPDATE_PENDING_NEW = 2
