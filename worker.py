#!/usr/bin/env python3

import click
import sys
from bookie.config import loadConfig
from redis import Redis
from rq import Connection, Worker
from bookie import log


@click.command()
@click.option("--config", default="config.yaml")
def main(config):
    config = loadConfig(config)

    redis = Redis(
        config.get("redis_host", 'localhost') or "localhost",
        config.get("redis_port", 6379) or 6379,
        password=config.get("redis_password"),
        db=config.get("redis_db", 0) or 0
    )
    log.info("Opening Redis connection (redis://:{}@{}/{})".format(
        config.get("redis_password"),
        config.get("redis_host", 'localhost') or "localhost",
        config.get("redis_port", 6379) or 6379,
        config.get("redis_db", 0) or 0
    ))
    with Connection(redis):
        w = Worker(sys.argv[1:] or ['default'])
        w.work()


if __name__ == "__main__":
    main()
