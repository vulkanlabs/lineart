import base64
from typing import Annotated

import requests
from fastapi import APIRouter, Body, Depends, HTTPException
from sqlalchemy.orm import Session
from vulkan_public.schemas import DataSourceCreate

from vulkan_server import schemas
from vulkan_server.auth import get_project_id
from vulkan_server.data.broker import DataBroker
from vulkan_server.data.io import DataSourceModelSerializer
from vulkan_server.db import DataSource, get_db
from vulkan_server.logger import init_logger

logger = init_logger("data")

sources = APIRouter(
    prefix="/data-sources",
    tags=["data-sources"],
    responses={404: {"description": "Not found"}},
)


@sources.get("/", response_model=list[schemas.DataSource])
def list_data_sources(
    project_id: str = Depends(get_project_id),
    db: Session = Depends(get_db),
):
    data_sources = db.query(DataSource).filter_by(project_id=project_id).all()
    response = [DataSourceModelSerializer.deserialize(ds) for ds in data_sources]
    return response


@sources.post("/")
def create_data_source(
    config: DataSourceCreate,
    project_id: str = Depends(get_project_id),
    db: Session = Depends(get_db),
):
    data_source: DataSource = DataSourceModelSerializer.serialize(config, project_id)
    db.add(data_source)
    db.commit()

    return {"data_source_id": data_source.data_source_id}


@sources.get("/{data_source_id}", response_model=schemas.DataSource)
def get_data_source(
    data_source_id: str,
    project_id: str = Depends(get_project_id),
    db: Session = Depends(get_db),
):
    data_source = (
        db.query(DataSource)
        .filter_by(data_source_id=data_source_id, project_id=project_id)
        .first()
    )
    if data_source is None:
        raise HTTPException(status_code=404, detail="Data source not found")

    response = DataSourceModelSerializer.deserialize(data_source)
    return response


broker = APIRouter(
    prefix="/data-broker",
    tags=["data-broker"],
    responses={404: {"description": "Not found"}},
)


@broker.post("/")
def get_data_object(
    data_source_id: Annotated[str, Body(embed=True)],
    request_body: Annotated[dict, Body(embed=True)],
    db: Session = Depends(get_db),
):
    # TODO: Control access to the data source by project_id
    data_source = db.query(DataSource).filter_by(data_source_id=data_source_id).first()
    if data_source is None:
        raise HTTPException(status_code=404, detail="Data source not found")

    spec: schemas.DataSource = DataSourceModelSerializer.deserialize(data_source)
    broker = DataBroker(db, spec)

    try:
        # TODO: handle different types of data
        data = broker.get_data(request_body)
        value = base64.b64decode(data.value)
    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch data: {str(e)}",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {"data": value}
