import logging
import time
from datetime import datetime

from flask import Flask, jsonify
from flask.globals import request
from flask.templating import render_template

from models import Gym

logging.basicConfig(format='%(asctime)s [%(module)10s] [%(levelname)5s] %(message)s')
logging.getLogger("peewee").setLevel(logging.INFO)
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

app = Flask(__name__)


@app.route('/')
def index():
    return render_template("map.html")


@app.route('/gyms')
def gyms():
    timestamp = int(request.args.get('after', 0))
    gyms = Gym.select().where(Gym.last_updated > datetime.fromtimestamp(timestamp + 1))
    last_updated = 0

    log.debug("Gyms: timestamp=%d %d" % (timestamp, len(gyms)))

    for gym in gyms:
        last_updated = max(last_updated, int(time.mktime(gym.last_updated.timetuple())))

    if not gyms:
        last_updated = timestamp
    return jsonify(timestamp=last_updated, gyms=[gym.serialize() for gym in gyms])


app.run(debug=True)
