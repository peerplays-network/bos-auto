#!/usr/bin/env python3

import threading
import click

from rq import Connection, Worker, use_connection, Queue
from bos_incidents import factory

from . import INCIDENT_CALLS
from .log import log
from .config import loadConfig


config = loadConfig()


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
@click.option(
    "--scheduler/--no-scheduler",
    default=True
)
def api(port, host, debug, proposer, approver, scheduler):
    """ Start the API endpoint
    """
    if scheduler:
        from .schedule import scheduler as start_scheduler
        from bookied.web import background_threads
        background_threads.append(threading.Thread(name="scheduler", target=start_scheduler))
        for t in background_threads:
            log.info("Starting thread for {}".format(t))
            t.start()

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
    from .redis_con import get_redis
    from . import work

    work.unlock()
    # Let's drop the redis database and refill it from incident store
    with Connection(get_redis()):

        q = Queue("failed")
        if q.count > 0:
            log.info("Emptying Redis Queue (failed) ...")
            q.empty()
            job = q.dequeue()
            while job is not None:
                log.info("Canceling " + str(job))
                job.cancel()
                job.delete()
                job = q.dequeue()

        q = Queue("default")
        count_before = q.count

        if q.count > 0:
            log.info("Emptying Redis Queue (default) ...")
            q.empty()
            job = q.dequeue()
            while job is not None:
                log.info("Canceling " + str(job))
                job.cancel()
                job.delete()
                job = q.dequeue()
            log.info("Redis Queue cleared (jobs before=" + str(count_before) + ")")
        else:
            log.info("Empty Redis Queue initialized")

    # This runs the Worker as thread
    with Connection(get_redis()):
        w = Worker([queue])
        w.work()


@main.command()
@click.option(
    "--proposer",
    default=config.get("BOOKIE_PROPOSER")
)
@click.option(
    "--approver",
    default=config.get("BOOKIE_APPROVER")
)
def approve(proposer, approver):
    """ Send an approve ticket to the queue
    """
    from .redis_con import get_redis
    from . import work
    redis = get_redis()
    work.unlock()
    use_connection(redis)
    q = Queue(connection=redis)
    q.enqueue(
        work.approve,
        args=(),
        kwargs=dict(
            proposer=proposer,
            approver=approver
        )
    )


@click.option(
    "--proposer"
)
@click.option(
    "--approver"
)
@main.command()
def scheduler(proposer, approver):
    """ Test for postponed incidents and process them
    """
    """
    from bos_incidents import factory
    from .schedule import check_scheduled
    storage = factory.get_incident_storage()
    check_scheduled(storage, func_callback=print)
    """
    from .schedule import scheduler
    scheduler(
        proposer=proposer,
        approver=approver,
    )


if __name__ == "__main__":
    main()
