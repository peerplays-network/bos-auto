import logging
from logging.handlers import SMTPHandler, RotatingFileHandler
from colorlog import ColoredFormatter
from .config import loadConfig

HAS_TELEGRAM = False
try:
    import telegram_handler
    HAS_TELEGRAM = True
except:
    pass


# Load config file
config = loadConfig()

# Enable logging
USE_TELEGRAM = (
    bool(HAS_TELEGRAM) and
    "telegram_token" in config and
    config["telegram_token"] and
    "telegram_chatid" in config and
    config["telegram_chatid"]
)
USE_MAIL = ("mailto" in config)
USE_STREAM = True
USE_FILE = False


def log_stream(logger):
    """ Log content in the output/syslog
    """
    if USE_STREAM:
        formatter = ColoredFormatter(LOGFORMAT)
        stream = logging.StreamHandler()
        stream.setLevel(LOG_LEVEL)
        stream.setFormatter(formatter)
        logger.addHandler(stream)


def log_file(logger):
    """ Log content to a file
    """
    if USE_FILE:
        log_handler_rotate = RotatingFileHandler(
            'bookied.log',
            maxBytes=1024 * 1024 * 100,
            backupCount=20
        )
        log_handler_rotate.setLevel(logging.INFO)
        logger.addHandler(log_handler_rotate)


def log_mail(logger):
    """ Send an email for logging
    """
    if USE_MAIL:
        # Mail
        log_handler_mail = SMTPHandler(
            config.get("mailhost", "localhost"),
            config.get("mailfrom", "bookied@example.com"),
            config.get("mailto"),
            config.get("mailsubject", "BookieD notification mail"))
        log_handler_mail.setFormatter(logging.Formatter(
            "Message type:       %(levelname)s\n" +
            "Location:           %(pathname)s:%(lineno)d\n" +
            "Module:             %(module)s\n" +
            "Function:           %(funcName)s\n" +
            "Time:               %(asctime)s\n" +
            "\n" +
            "Message:\n" +
            "\n" +
            "%(message)s\n"
        ))
        log_handler_mail.setLevel(logging.WARNING)
        logger.addHandler(log_handler_mail)


def log_telegram(logger):
    """ Enable logging via Telegram
    """
    if USE_TELEGRAM:
        tgHandler = telegram_handler.TelegramHandler(
            token=config.get("telegram_token"),
            chat_id=config.get("telegram_chatid")
        )
        tgHandler.setLevel(logging.WARNING)
        logger.addHandler(tgHandler)


# Default logging facilities
LOG_LEVEL = logging.INFO
LOGFORMAT = ("  %(log_color)s%(levelname)-8s%(reset)s |"
             " %(log_color)s%(message)s%(reset)s")
logging.root.setLevel(LOG_LEVEL)
formatter = ColoredFormatter(LOGFORMAT)

log = logging.getLogger(__name__)
log.setLevel(LOG_LEVEL)

logsync = logging.getLogger("bookied_sync")
logsync.setLevel(LOG_LEVEL)

for logger in [log, logsync]:
    log_stream(logger)
    log_file(logger)
    log_mail(logger)
    log_telegram(logger)

# Enable full logging
# logging.basicConfig(level=logging.DEBUG)
