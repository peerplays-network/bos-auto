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

# Default logging facilities
LOG_LEVEL = logging.DEBUG
LOGFORMAT = ("  %(log_color)s%(levelname)-8s%(reset)s |"
             " %(log_color)s%(message)s%(reset)s")
logging.root.setLevel(LOG_LEVEL)
log = logging.getLogger(__name__)
log.setLevel(LOG_LEVEL)

# Enable logging
USE_TELEGRAM = (bool(HAS_TELEGRAM) and "telegram_token" in config and "telegram_chatid" in config)
USE_MAIL = ("mailto" in config)
USE_STREAM = True
USE_FILE = True

if USE_STREAM:
    formatter = ColoredFormatter(LOGFORMAT)
    stream = logging.StreamHandler()
    stream.setLevel(LOG_LEVEL)
    stream.setFormatter(formatter)
    log.addHandler(stream)

if USE_FILE:
    log_handler_rotate = RotatingFileHandler(
        '%s.log' % config.project_name,
        maxBytes=1024 * 1024 * 100,
        backupCount=20
    )
    log_handler_rotate.setLevel(logging.INFO)
    log.addHandler(log_handler_rotate)

if USE_MAIL:
    # Mail
    log_handler_mail = SMTPHandler(
        config.get("mailhost", "localhost"),
        config.get("mailfrom", "bookied@localhost"),
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
    log.addHandler(log_handler_mail)

if USE_TELEGRAM:
    tgHandler = telegram_handler.TelegramHandler(
        token=config.get("telegram_token"),
        chat_id=config.get("telegram_chatid")
    )
    tgHandler.setLevel(logging.WARNING)
    log.addHandler(tgHandler)

# logging.basicConfig(level=logging.DEBUG)
