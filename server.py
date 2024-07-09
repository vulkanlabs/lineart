from flask import Flask, request

app = Flask(__name__)

db = {
    "1": {
        "name": "Alice",
        "serasa": 100,
        "scr": 200,
    },
    "2": {
        "name": "Bob",
        "serasa": 300,
        "scr": 400,
    },
    "3": {
        "name": "Charlie",
        "serasa": 500,
        "scr": 600,
    },
    "4": {
        "name": "David",
        "serasa": 700,
        "scr": 800,
    },
    "5": {
        "name": "Eve",
        "serasa": 900,
        "scr": 1000,
    },
}


@app.route("/scr")
def scr_data():
    print(request.form)
    cpf = request.form["cpf"]
    entry = db[cpf]
    response = {
        "score": entry["scr"],
    }
    return response


@app.route("/serasa")
def serasa_data():
    print(request.form)
    cpf = request.form["cpf"]
    entry = db[cpf]
    response = {
        "score": entry["serasa"],
    }
    return response
