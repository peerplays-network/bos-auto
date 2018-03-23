from rq import use_connection, Queue
from flask import Flask, request, jsonify
from jsonschema import validate
from .endpointschema import schema
from .config import loadConfig
from . import work
from .redis_con import redis
from . import log

config = loadConfig()

# Flask app and parameters
app = Flask(__name__)
use_connection(redis)
q = Queue(connection=redis)


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
    """
    if request.method == 'POST':
        # Obtain message from request body
        j = request.get_json()

        # Ensure it is json
        try:
            validate(j, schema)
        except Exception:
            return "Invalid data format", 503

        # Make sure it has the proper format
        if any([x not in j for x in ["id", "call", "arguments"]]):
            return "Insufficient data provided", 503

        for key in ["id", "arguments"]:
            if not isinstance(j.get(key), dict):
                return "{} needs to be a dictionary".format(
                    key), 503

        # Send to redis
        job = q.enqueue(
            work.process,
            args=(j,),
            kwargs=dict(
                proposer=app.config.get("BOOKIE_PROPOSER"),
                approver=app.config.get("BOOKIE_APPROVER")
            )
        )

        log.info("Forwarded incident to worker via redis")

        # In case we "proposed" something, we also need to approve,
        # we do that by queuing a selfapprove
        approve_job = q.enqueue(
            work.selfapprove,
            args=(),
            kwargs=dict(
                proposer=config.get("BOOKIE_PROPOSER"),
                approver=config.get("BOOKIE_APPROVER")
            )
        )


        # Return message with id
        return jsonify(dict(
            result="processing",
            message=j,
            id=job.id,
            id_approve=approve_job.id
        ))

    return "", 503
