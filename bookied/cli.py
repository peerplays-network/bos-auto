#!/usr/bin/env python3

import click
import sys
from redis import Redis
from rq import Connection, Worker
from .config import loadConfig
from . import log


@click.group()
def main():
    """ Main group for python-click so we can offer subcommands in a single cli
        tool
    """
    pass


@main.command()
@click.option(
    "--port",
    type=int,
    default=8010
)
@click.option(
    "--host",
    type=str,
    default="127.0.0.1"
)
@click.option(
    "--host",
    type=str,
    default="127.0.0.1"
)
@click.option(
    '--debug',
    is_flag=True,
    default=False
)
@click.option(
    "--proposer"
)
@click.option(
    "--approver"
)
def api(port, host, debug, proposer, approver):
    """ Start the API endpoint
    """
    from bookied.web import app
    app.config["BOOKIE_PROPOSER"] = proposer
    app.config["BOOKIE_APPROVER"] = approver
    app.run(
        host=host,
        port=port,
        debug=debug
    )


@main.command()
@click.option("--config", default="config.yaml")
def worker(config):
    """ Start the (redis queue) worker to deal with the received messages
    """
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
