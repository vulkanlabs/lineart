from fastapi import FastAPI
from pydantic import BaseModel

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


class Entity(BaseModel):
    tax_id: str


@app.get("/scr")
def scr_data(entity: Entity):
    tax_id = entity.tax_id
    entry = db[tax_id]
    response = {
        "score": entry["scr"],
    }
    return response


@app.get("/serasa")
def serasa_data(entity: Entity):
    tax_id = entity.tax_id
    entry = db[tax_id]
    response = {
        "score": entry["serasa"],
    }
    return response
