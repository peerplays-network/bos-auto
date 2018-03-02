from redis import Redis
from .config import loadConfig
from . import log

config = loadConfig()

redis = Redis(
    config.get("redis_host", 'localhost') or "localhost",
    config.get("redis_port", 6379) or 6379,
    password=config.get("redis_password"),
    db=config.get("redis_db", 0) or 0
)
log.info("Opening Redis connection (redis://:{}@{}/{})".format(
    config.get("redis_password", None) or None,
    config.get("redis_host", 'localhost') or "localhost",
    config.get("redis_port", 6379) or 6379,
    config.get("redis_db", 0) or 0
))
