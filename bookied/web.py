import pkg_resources
from rq import use_connection, Queue
from flask import Flask, request, jsonify
from jsonschema import validate
from . import work
from .endpointschema import schema
from .config import loadConfig
from .redis_con import get_redis
from .log import log
from .utils import resolve_hostnames
from bos_incidents import factory, exceptions

config = loadConfig()

# Flask app and parameters
app = Flask(__name__)
redis = get_redis()
use_connection()

# Flask queue
q = Queue(connection=redis)

# Invident Storage
storage = factory.get_incident_storage()

# API whitelist
api_whitelist = resolve_hostnames(config.get("api_whitelist", ["0.0.0.0"]))


@app.route('/')
def home():
    """ Let's not expose that this is a bos-auto endpoint
    """
    return "", 404


@app.route("/isalive")
def isalive():
    versions = dict()
    for name in ["bos-mint", "peerplays", "bookiesports"]:
        try:
            versions["name"] = pkg_resources.require(name)[0].version
        except Exception:
            versions["name"] = "not installed"
    return jsonify({'versions': versions})


@app.route('/trigger', methods=["GET", "POST"])
def trigger():
    """ This endpoint is used to submit data to the queue so we can process it
        asynchronously to the web requests. The webrequests should be answered
        fast, while the processing might take more time

        The endpoint opens an API according to the ``--port`` and ``--host``
        settings on launch. Thise API provides an endpoint on

            /trigger

        and consumes POST messages with JSON formatted body.

        The body is validated against the :doc:`schema`.

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
            validate(incident, schema)
        except Exception:
            log.error(
                "Received invalid request: {}".format(str(incident))
            )
            return "Invalid data format", 503

        # Try insert the incident into the database
        # We insert incidents right here so we still have them even if the
        # worker daemon crashes
        if not incident.get("skip_storage", False):
            try:
                # FIXME, remove copy()
                storage.insert_incident(incident.copy())
            except exceptions.DuplicateIncidentException:
                # We merely pass here since we have the incident already
                # alerting anyone won't do anything
                pass

        # Send incident to redis
        job = q.enqueue(
            work.process,
            args=(incident,),
            kwargs=dict(
                proposer=app.config.get("BOOKIE_PROPOSER"),
                approver=app.config.get("BOOKIE_APPROVER")
            )
        )
        log.info(
            "Forwarded incident {} to worker via redis".format(
                incident.get("call")))

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
