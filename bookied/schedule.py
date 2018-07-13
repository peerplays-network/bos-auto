import threading
import time
from datetime import datetime

from rq import Queue
from bos_incidents import factory

from . import INCIDENT_CALLS
from .log import log
from .config import loadConfig
from .redis_con import get_redis

config = loadConfig()


def check_scheduled(
    storage=None,
    func_callback=None,
    proposer=None,
    approver=None,
):
    """
    """
    log.info(
        "Scheduler checking incidents database ... "
        "(approver: {}/ proposer: {})".format(
            approver, proposer))

    # Flask queue
    q = Queue(connection=get_redis())

    # Invident Storage
    if not storage:
        storage = factory.get_incident_storage()

    if not proposer:
        proposer = config.get("BOOKIE_PROPOSER")
    if not approver:
        approver = config.get("BOOKIE_APPROVER")

    for call in INCIDENT_CALLS:
        log.info("- testing call {}".format(call))
        events = storage.get_events_by_call_status(
            call=call,
            status_name="postponed",
            status_expired_before=datetime.utcnow())
        events = list(events)

        ids = list()
        for event in events:
            for incidentid in event.get(call, {}).get("incidents", []):
                incident = storage.resolve_to_incident(incidentid)

                log.info("Scheduler retriggering incident ...")
                if func_callback:
                    print("!")
                    job = q.enqueue(
                        func_callback,
                        args=(incident,),
                        kwargs=dict(
                            proposer=proposer,
                            approver=approver
                        )
                    )
                    ids.append(job.id)

    return ids


class PeriodicExecutor(threading.Thread):
    """
    """

    def __init__(self, sleep, func, *args, **kwargs):

        """ execute func(params) every 'sleep' seconds """
        self.func = func
        self.sleep = sleep
        self.args = args
        self.kwargs = kwargs
        threading.Thread.__init__(
            self,
            name="PeriodicExecutor")
        self.setDaemon(1)

    def run(self):
        while 1:
            time.sleep(self.sleep)
            self.func(*self.args, **self.kwargs)


def scheduler(
    delay=None,
    proposer=None,
    approver=None,
):
    """
    """
    from . import work
    if not delay:
        delay = config["scheduler"]["interval"]

    if not proposer:
        proposer = config.get("BOOKIE_PROPOSER")
    if not approver:
        approver = config.get("BOOKIE_APPROVER")

    check_scheduled(
        storage=None,
        func_callback=work.process,
        proposer=proposer,
        approver=approver
    )

    PeriodicExecutor(
        delay,
        check_scheduled,
        storage=None,
        func_callback=work.process,
        proposer=proposer,
        approver=approver
    ).run()
