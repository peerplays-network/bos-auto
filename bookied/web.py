from rq import use_connection, Queue
from flask import Flask, request, jsonify
from jsonschema import validate
from . import work
from .endpointschema import schema
from .config import loadConfig
from .redis_con import redis
from .log import log
from bos_incidents import factory, exceptions

config = loadConfig()

# Flask app and parameters
app = Flask(__name__)
use_connection(redis)

# Flask queue
q = Queue(connection=redis)

# Invident Storage
storage = factory.get_incident_storage()


@app.route('/')
def home():
    return "", 404


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
        try:
            storage.insert_incident(incident.copy())  # FIXME, remove copy()
        except exceptions.DuplicateIncidentException:
            log.warn("Incident already received!")
            """ FIXME
            return "Incident already received", 503
            """

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
