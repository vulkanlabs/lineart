from typing import Annotated

from fastapi import FastAPI, Form, Body

app = FastAPI()

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


@app.get("/")
def get_data(tax_id: Annotated[str, Body(embed=True)]):
    entry = db[tax_id]
    response = {
        "name": entry["name"],
        "serasa": entry["serasa"],
        "scr": entry["scr"],
    }
    return response


@app.get("/scr")
def scr_data(tax_id: Annotated[str, Form()]):
    entry = db[tax_id]
    response = {
        "score": entry["scr"],
    }
    return response


@app.get("/serasa")
def serasa_data(tax_id: Annotated[str, Form()]):
    entry = db[tax_id]
    response = {
        "score": entry["serasa"],
    }
    return response
