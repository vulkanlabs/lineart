import logging
import sys
from typing import Annotated

from fastapi import Body, FastAPI, Form, Request

app = FastAPI()

logger = logging.getLogger("uvicorn.error")
stream_handler = logging.StreamHandler(sys.stdout)
logger.addHandler(stream_handler)

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
def get_data(
    request: Request, tax_id: Annotated[str, Body(embed=True)], full: bool = False
):
    logger.info(f"Request headers: {request.headers}")
    entry = db[tax_id]
    response = {"serasa": entry["serasa"], "scr": entry["scr"]}
    if full:
        response["name"] = entry["name"]
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
