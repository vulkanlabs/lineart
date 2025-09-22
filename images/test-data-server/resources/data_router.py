import logging
from typing import Annotated

from fastapi import APIRouter, Body, Response
from pydantic import BaseModel

# Create router for data server endpoints
router = APIRouter(prefix="/data", tags=["data"])

logger = logging.getLogger("uvicorn.error")


class SerasaResponse(BaseModel):
    score: int
    renda_presumida: float
    restricoes_qt: int
    restricoes_valor: float


class SCRResponse(BaseModel):
    score: int


# Original data server database
db = {
    "0": {
        "name": "Admin",
        "serasa": {
            "score": 0,
            "renda_presumida": 0.0,
            "restricoes_qt": 0,
            "restricoes_valor": 0.0,
        },
        "scr": {"score": 0},
    },
    "111.111.111-11": {
        "name": "Alice",
        "serasa": {
            "score": 100,
            "renda_presumida": 3500.0,
            "restricoes_qt": 1,
            "restricoes_valor": 850.0,
        },
        "scr": {"score": 200},
    },
    "222.222.222-22": {
        "name": "Bob",
        "serasa": {
            "score": 300,
            "renda_presumida": 5200.0,
            "restricoes_qt": 2,
            "restricoes_valor": 1200.0,
        },
        "scr": {"score": 400},
    },
    "333.333.333-33": {
        "name": "Charlie",
        "serasa": {
            "score": 500,
            "renda_presumida": 7800.0,
            "restricoes_qt": 0,
            "restricoes_valor": 0.0,
        },
        "scr": {"score": 600},
    },
    "444.444.444-44": {
        "name": "David",
        "serasa": {
            "score": 700,
            "renda_presumida": 9500.0,
            "restricoes_qt": 3,
            "restricoes_valor": 2300.0,
        },
        "scr": {"score": 800},
    },
    "555.555.555-55": {
        "name": "Eve",
        "serasa": {
            "score": 900,
            "renda_presumida": 12000.0,
            "restricoes_qt": 1,
            "restricoes_valor": 500.0,
        },
        "scr": {"score": 1000},
    },
}


@router.post("/scr", response_model=SCRResponse)
def scr_data(cpf: Annotated[str, Body(embed=True)]):
    """Get SCR score data"""
    entry = db.get(cpf, None)
    if entry is None:
        return Response(status=404)
    scr_data = entry["scr"]
    response = SCRResponse.model_validate(scr_data)
    return response


@router.post("/serasa", response_model=SerasaResponse)
def serasa_data(cpf: Annotated[str, Body(embed=True)]):
    """Get Serasa score data"""
    entry = db.get(cpf, None)
    if entry is None:
        return Response(status=404)
    serasa_data = entry["serasa"]
    response = SerasaResponse.model_validate(serasa_data)
    return response
