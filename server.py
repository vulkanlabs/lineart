from flask import Flask

app = Flask(__name__)


@app.route("/")
def hello_world():
    response = {
        "message": "Hello, World!",
        "score": 100,
    }
    return response
