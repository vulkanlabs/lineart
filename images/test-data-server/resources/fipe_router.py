import logging
from datetime import date
from typing import Annotated

from fastapi import APIRouter, Body
from pydantic import BaseModel

# Create router for FIPE endpoints
router = APIRouter(prefix="/fipe", tags=["fipe"])

logger = logging.getLogger("uvicorn.error")


class VehicleRequest(BaseModel):
    marca: str
    modelo: str
    ano: str | int
    codigo_fipe: str | None = None


class FipeResponse(BaseModel):
    mes_referencia: date
    codigo_fipe: str
    marca: str
    modelo: str
    ano_modelo: str
    data_consulta: date
    valor_medio: float


# Mock database with vehicle pricing data
fipe_db = {
    ("VOLKSWAGEN", "GOL", "2020"): {"codigo_fipe": "005004-1", "valor_medio": 45000.00},
    ("FORD", "FIESTA", "2019"): {"codigo_fipe": "003025-7", "valor_medio": 42000.00},
    ("CHEVROLET", "ONIX", "2021"): {"codigo_fipe": "002010-3", "valor_medio": 55000.00},
    ("TOYOTA", "COROLLA", "2022"): {
        "codigo_fipe": "001045-9",
        "valor_medio": 120000.00,
    },
    ("HONDA", "CIVIC", "2020"): {"codigo_fipe": "004030-2", "valor_medio": 95000.00},
    ("FIAT", "UNO", "2018"): {"codigo_fipe": "006015-4", "valor_medio": 35000.00},
    ("NISSAN", "MARCH", "2019"): {"codigo_fipe": "007020-8", "valor_medio": 38000.00},
    ("HYUNDAI", "HB20", "2021"): {"codigo_fipe": "008012-6", "valor_medio": 52000.00},
}


@router.post("/", response_model=FipeResponse)
def get_fipe_price(vehicle: Annotated[VehicleRequest, Body()]):
    """
    Get FIPE price for a vehicle based on brand, model, and year.
    """
    logger.info(f"FIPE request for: {vehicle.marca} {vehicle.modelo} {vehicle.ano}")

    # Normalize the search key
    search_key = (vehicle.marca.upper(), vehicle.modelo.upper(), str(vehicle.ano))

    # Look up vehicle in database
    if search_key in fipe_db:
        vehicle_data = fipe_db[search_key]
        codigo_fipe = vehicle_data["codigo_fipe"]
        valor_medio = vehicle_data["valor_medio"]
    else:
        # Default values for unknown vehicles
        codigo_fipe = "999999-0"
        valor_medio = 25000.00
        logger.warning(f"Vehicle not found in database: {search_key}")

    # Get current date for reference month and query date
    today = date.today()

    response = FipeResponse(
        mes_referencia=today.replace(day=1),  # First day of current month
        codigo_fipe=codigo_fipe,
        marca=vehicle.marca.upper(),
        modelo=vehicle.modelo.upper(),
        ano_modelo=str(vehicle.ano),
        data_consulta=today,
        valor_medio=valor_medio,
    )

    return response
