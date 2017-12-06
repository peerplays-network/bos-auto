from flask import Flask, request, jsonify
from flask_rq import RQ, get_queue
from . import work

# Flask app and parameters
app = Flask(__name__)
app.config['RQ_OTHER_HOST'] = 'localhost'
app.config['RQ_OTHER_PORT'] = 6379
app.config['RQ_OTHER_PASSWORD'] = None
app.config['RQ_OTHER_DB'] = 0

# Flask based Redis Queue
rq = RQ(app)


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
        q = get_queue()
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
