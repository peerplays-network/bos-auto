#!/usr/bin/env python3

import click
from rq import Connection, Worker, use_connection, Queue


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
@click.argument("queue", default="default")
def worker(queue):
    """ Start the (redis queue) worker to deal with the received messages
    """
    from .redis_con import redis
    with Connection(redis):
        w = Worker([queue])
        w.work()


@main.command()
def selfapprove():
    from .redis_con import redis
    from . import work
    from .config import loadConfig
    config = loadConfig()
    use_connection(redis)
    q = Queue(connection=redis)
    q.enqueue(
        work.selfapprove,
        args=(),
        kwargs=dict(
            proposer=config.get("BOOKIE_PROPOSER"),
            approver=config.get("BOOKIE_APPROVER")
        )
    )


if __name__ == "__main__":
    main()
