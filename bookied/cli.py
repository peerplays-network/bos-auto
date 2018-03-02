#!/usr/bin/env python3

import click
import sys
from rq import Connection, Worker
from .config import loadConfig


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
@click.argument("queue", default="default")
def worker(config, queue):
    """ Start the (redis queue) worker to deal with the received messages
    """
    config = loadConfig(config)
    from .redis_con import redis
    with Connection(redis):
        w = Worker([queue])
        w.work()


if __name__ == "__main__":
    main()
