import threading
import time
from datetime import datetime

from rq import Queue
from bos_incidents import factory

from . import work
# from .log import log
from .config import loadConfig
from .redis_con import get_redis

config = loadConfig()


def check_scheduled(storage=None):
    """
    """

    # Flask queue
    q = Queue(connection=get_redis())

    # Invident Storage
    if not storage:
        storage = factory.get_incident_storage()

    events = storage.get_events_by_call_status(
        call="create",
        status_name="postponed",
        status_expired_before=datetime.utcnow())
    events = list(events)

    ids = list()
    for event in events:
        for incidentid in event.get("create", {}).get("incidents", []):
            incident = storage.resolve_to_incident(incidentid)

            job = q.enqueue(
                work.process,
                args=(incident,),
                kwargs=dict(
                    proposer=config.get("BOOKIE_PROPOSER"),
                    approver=config.get("BOOKIE_APPROVER")
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


def scheduler(delay=30):
    """
    """
    check_scheduled()
    PeriodicExecutor(delay, check_scheduled).run()
