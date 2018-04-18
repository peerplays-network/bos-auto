import time
from rq import use_connection, Queue
from . import work
from .config import loadConfig
from .redis_con import redis
from .log import log
from bos_incidents import factory, exceptions
import threading

config = loadConfig()


def check_scheduled():

    print("foobar")
    return

    # Flask queue
    q = Queue(connection=redis)

    # Invident Storage
    storage = factory.get_incident_storage()

    incident = {}
    try:
        storage.insert_incident(incident)
    except exceptions.DuplicateIncidentException:
        log.info("Incident already received!")
        return "Incident already received", 503
    """

    job = q.enqueue(
        work.process,
        args=(incident,),
        kwargs=dict(
            proposer=app.config.get("BOOKIE_PROPOSER"),
            approver=app.config.get("BOOKIE_APPROVER")
        )
    )
    """


class PeriodicExecutor(threading.Thread):

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
    check_scheduled()
    PeriodicExecutor(delay, check_scheduled).run()
