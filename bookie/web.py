from redis import Redis
from rq import use_connection, Queue
from flask import Flask, request, jsonify
from . import work
from .config import config

# Flask app and parameters
app = Flask(__name__)
redis = Redis(
    config.get("redis_host", 'localhost'),
    config.get("redis_port", 6379),
    password=config.get("redis_password")
)
use_connection(redis)
q = Queue(connection=redis)


@app.route('/', methods=["GET", "POST"])
def home():
    """ This endpoint is used to submit data to the queue so we can process it
        asynchronously to the web requests. The webrequests should be answered
        fast, while the processing might take more time
    """
    if request.method == 'POST':
        # Obtain message from request body
        j = request.get_json()

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
            kwargs=dict()
        )

        # Return message with id
        return jsonify(dict(
            result="processing",
            message=j,
            id=job.id))

    return "", 503

