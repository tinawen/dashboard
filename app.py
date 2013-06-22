from flask import Flask, render_template
from werkzeug.contrib.fixers import ProxyFix
from gapi import (get_latitude_info,
                  get_calendar_info,
                  get_tasks_info)
from capture import take_picture, WEBCAM_PICTURE_FOLDER
import glob
import os
import json

app = Flask(__name__)

@app.route("/")
def dashboard():
    return render_template('index.jinja2')

@app.route('/location', methods=["GET"])
def location():
    return get_latitude_info()

@app.route('/calendar', methods=["GET"])
def calendar():
    return get_calendar_info()

@app.route('/tasks', methods=["GET"])
def tasks():
    return get_tasks_info()

@app.route('/picture', methods=["GET"])
def picture():
    files = filter(os.path.isfile, glob.glob(WEBCAM_PICTURE_FOLDER + "*"))
    if len(files) > 0:
        files.sort(key=lambda x: os.path.getmtime(x))
        return json.dumps('./static/img/webcam/%s' % os.path.basename(files[len(files)-1]))
    return take_picture()

app.wsgi_app = ProxyFix(app.wsgi_app)

if __name__ == "__main__":
    app.debug = True
    app.run('0.0.0.0')
