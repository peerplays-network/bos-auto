
import pkg_resources
from rq import use_connection, Connection, Queue
from flask import Flask, request, jsonify

from . import work
from .config import loadConfig
from .redis_con import get_redis
from .utils import resolve_hostnames
from bos_incidents import factory, exceptions
from bos_incidents.validator import IncidentValidator, InvalidIncidentFormatException
from bookiesports.normalize import IncidentsNormalizer, NotNormalizableException

from .log import log
from . import INCIDENT_CALLS

config = loadConfig()

# Flask app and parameters
app = Flask(__name__)
redis = get_redis()
use_connection(redis)

# Invident Storage
storage = factory.get_incident_storage()

validator = IncidentValidator()

# API whitelist
api_whitelist = resolve_hostnames(config.get("api_whitelist", ["0.0.0.0"]))

background_threads = []


@app.route('/')
def home():
    """ Let's not expose that this is a bos-auto endpoint
    """
    return "", 404


@app.route("/isalive")
def isalive():

    versions = dict()
    for name in [
        "bos-auto",
        "peerplays",
        "bookiesports",
        "bos-incidents",
        "bos-sync"
    ]:
        try:
            versions[name] = pkg_resources.require(name)[0].version
        except Exception:
            versions[name] = "not installed"
    # queue status
    queue_status = {}
    with Connection(redis):
        q = Queue(connection=redis)
        for queue in q.all():
            queue_status[queue.name] = dict(
                count=queue.count,
            )

    background_threads_dict = {}
    for t in background_threads:
        try:
            background_threads_dict[t.name] = {"running": t.is_alive()}
        except Exception as e:
            log.error(
                "Error in background task: {}".format(str(e))
            )

    return jsonify(dict(
        versions=versions,
        queue=dict(status=queue_status),
        background=background_threads_dict
    ))


@app.route("/events")
@app.route("/events/<event_id>")
def events(event_id=None):
    if event_id is not None:
        event = storage.get_event_by_id(event_id, True, True)
        event.pop("_id")
        return jsonify(
            dict(event)
        )
    else:
        return jsonify(
            storage.get_incidents_count()
        )


@app.route("/finalize")
def finalize():
    # only added for debugging
    for call in INCIDENT_CALLS:
        log.info("- querying call for finalizing {}".format(call))
        events = []
        for status_name in [
            "connection lost",
            "unknown",
            "postponed",
            "unhandled exception, retrying soon"
        ]:
            for event in storage.get_events_by_call_status(
                    call=call,
                    status_name=status_name
            ):
                events.append(event)

        log.info("Finalizing " + str(len(events)) + " events ...")
        for event in events:
            storage.update_event_status_by_id(event["id_string"], call=call, status_name="manually finalized")


@app.route("/finalize/purge")
def finalize_purge():
    storage = factory.get_incident_storage(purge=True)
    return "success"


@app.route('/trigger', methods=["GET", "POST"])
def trigger():
    """ This endpoint is used to submit data to the queue so we can process it
        asynchronously to the web requests. The webrequests should be answered
        fast, while the processing might take more time

        The endpoint opens an API according to the ``--port`` and ``--host``
        settings on launch. Thise API provides an endpoint on

            /trigger

        and consumes POST messages with JSON formatted body.

        The body is validated against the incident schema defined in
        bos-incidents

        .. note:: The trigger endpoint stores the incidents through
                  (bos-incidents) already to allow later replaying.
    """
    if request.method == 'POST':
        # Don't bother wit requests from IPs that are not
        # whitelisted
        if (
            request.remote_addr not in api_whitelist and
            "0.0.0.0" not in api_whitelist
        ):
            return "Your IP address is not allowed to post here!", 403

        # Obtain message from request body
        incident = request.get_json()

        # Ensure it is json
        try:
            validator.validate_incident(incident)
        except InvalidIncidentFormatException:
            log.error(
                "Received invalid request: {}".format(str(incident))
            )
            return "Invalid data format", 400

        # Only accept normalizable incidents
        # Normalize incident
        normalizer = IncidentsNormalizer(chain=config.get("network", "beatrice"))
        try:
            incident = normalizer.normalize(incident)
        except NotNormalizableException:
            log.warning(
                "Received not normalizable incident, discarding {}".format(str(incident))
            )
            return "Not normalized incident", 400

        try:
            # FIXME, remove copy()
            storage.insert_incident(incident.copy())
        except exceptions.DuplicateIncidentException as e:
            # We merely pass here since we have the incident already
            # alerting anyone won't do anything
            # traceback.print_exc()
            pass

        # Send incident to redis
        with Connection(redis):
            q = Queue(connection=redis)
            job = q.enqueue(
                work.process,
                args=(incident,),
                kwargs=dict(
                    proposer=app.config.get("BOOKIE_PROPOSER"),
                    approver=app.config.get("BOOKIE_APPROVER")
                )
            )
            log.info(
                "Forwarded incident {} to worker via redis".format(str(incident))
            )

            # In case we "proposed" something, we also need to approve,
            # we do that by queuing a approve
            approve_job = q.enqueue(
                work.approve,
                args=(),
                kwargs=dict(
                    proposer=app.config.get("BOOKIE_PROPOSER"),
                    approver=app.config.get("BOOKIE_APPROVER")
                )
            )

        # Return message with id
        return jsonify(dict(
            result="processing",
            message=incident,
            id=str(job.id),
            id_approve=str(approve_job.id)
        ))

    return "", 503
