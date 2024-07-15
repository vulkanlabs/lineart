from flask import Flask, request

app = Flask(__name__)


@app.route("/", methods=["POST"])
def root():
    print(request.form)
    return {}
