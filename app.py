from flask import Flask, render_template
from gapi import (get_latitude_info,
                  get_calendar_info,
                  get_tasks_info)
from capture import take_picture
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
    return take_picture()

if __name__ == "__main__":
    app.debug = True
    app.run(host='0.0.0.0')
