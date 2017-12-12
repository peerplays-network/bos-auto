#!/usr/bin/env python3

import sys
from bookie.config import config
from redis import Redis
from rq import Connection, Worker

redis = Redis(
    config.get("redis_host", 'localhost'),
    config.get("redis_port", 6379),
    password=config.get("redis_password")
)

with Connection(redis):
    w = Worker(sys.argv[1:] or ['default'])
    w.work()
