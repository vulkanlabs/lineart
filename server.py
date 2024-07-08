from flask import Flask
import numpy as np

app = Flask(__name__)


@app.route("/")
def hello_world():
    response = {
        "message": "Hello, World!",
        "score": 100,
    }
    return response


@app.route("/scr")
def scr_data():
    response = {
        "score": np.random.randint(0, 1000),
    }
    return response


@app.route("/serasa")
def serasa_data():
    response = {
        "score": np.random.randint(0, 1000),
    }
    return response
