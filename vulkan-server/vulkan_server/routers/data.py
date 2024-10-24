from typing import Annotated

import requests
from fastapi import APIRouter, Body, Depends, HTTPException
from sqlalchemy.orm import Session
from vulkan_public.schemas import DataSourceCreate

from vulkan_server import schemas
from vulkan_server.auth import get_project_id
from vulkan_server.data.broker import DataBroker
from vulkan_server.data.io import DataSourceModelSerializer
from vulkan_server.db import (
    ComponentDataDependency,
    ComponentVersion,
    DataObject,
    DataSource,
    PolicyDataDependency,
    PolicyVersion,
    get_db,
)
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
    include_archived: bool = False,
    db: Session = Depends(get_db),
):
    filters = dict(project_id=project_id)
    if not include_archived:
        filters["archived"] = False
    data_sources = db.query(DataSource).filter_by(**filters).all()
    response = [DataSourceModelSerializer.deserialize(ds) for ds in data_sources]
    return response


@sources.post("/")
def create_data_source(
    config: DataSourceCreate,
    project_id: str = Depends(get_project_id),
    db: Session = Depends(get_db),
):
    ds = db.query(DataSource).filter_by(name=config.name).first()
    if ds is not None:
        raise HTTPException(status_code=400, detail="Data source already exists")

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


@sources.delete("/{data_source_id}")
def delete_data_source(
    data_source_id: str,
    project_id: str = Depends(get_project_id),
    db: Session = Depends(get_db),
):
    # TODO: ensure this function can only be executed by ADMIN level users
    data_source = (
        db.query(DataSource)
        .filter_by(
            data_source_id=data_source_id,
            project_id=project_id,
            archived=False,
        )
        .first()
    )
    if data_source_id is None:
        msg = f"Tried to delete non-existent data source {data_source_id}"
        raise HTTPException(status_code=404, detail=msg)

    ds_component_uses = (
        db.query(ComponentDataDependency, ComponentVersion)
        .join(ComponentVersion)
        .filter(
            ComponentDataDependency.data_source_id == data_source_id,
            ComponentVersion.archived == False,  # noqa: E712
        )
        .all()
    )
    if len(ds_component_uses) > 0:
        msg = f"Data source {data_source_id} is used by one or more component versions"
        raise HTTPException(status_code=400, detail=msg)

    ds_policy_uses = (
        db.query(PolicyDataDependency, PolicyVersion)
        .join(PolicyVersion)
        .filter(
            PolicyDataDependency.data_source_id == data_source_id,
            PolicyVersion.archived == False,  # noqa: E712
        )
        .all()
    )
    if len(ds_policy_uses) > 0:
        msg = f"Data source {data_source_id} is used by one or more policy versions"
        raise HTTPException(status_code=400, detail=msg)

    objects = db.query(DataObject).filter_by(data_source_id=data_source_id).all()
    if len(objects) > 0:
        msg = f"Data source {data_source_id} has associated data objects"
        raise HTTPException(status_code=400, detail=msg)

    data_source.archived = True
    db.commit()
    logger.info(f"Archived data source {data_source_id}")
    return {"component_version_id": data_source_id}


@sources.get("/{data_source_id}/objects")
def list_data_objects(
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

    data_objects = db.query(DataObject).filter_by(data_source_id=data_source_id).all()
    return [
        dict(
            data_object_id=do.data_object_id,
            data_source_id=do.data_source_id,
            project_id=do.project_id,
            key=do.key,
            created_at=do.created_at,
        )
        for do in data_objects
    ]


@sources.get(
    "/{data_source_id}/objects/{data_object_id}", response_model=schemas.DataObject
)
def get_data_object(
    data_source_id: str,
    data_object_id: str,
    project_id: str = Depends(get_project_id),
    db: Session = Depends(get_db),
):
    data_object = (
        db.query(DataObject)
        .filter_by(data_object_id=data_object_id, project_id=project_id)
        .first()
    )
    if data_object is None:
        raise HTTPException(status_code=404, detail="Data object not found")

    return data_object


broker = APIRouter(
    prefix="/data-broker",
    tags=["data-broker"],
    responses={404: {"description": "Not found"}},
)


@broker.post("/", response_model=schemas.DataBrokerResponse)
def request_data_from_broker(
    data_source_name: Annotated[str, Body(embed=True)],
    request_body: Annotated[dict, Body(embed=True)],
    db: Session = Depends(get_db),
):
    # TODO: Control access to the data source by project_id
    data_source = db.query(DataSource).filter_by(name=data_source_name).first()
    if data_source is None:
        raise HTTPException(status_code=404, detail="Data source not found")

    spec: schemas.DataSource = DataSourceModelSerializer.deserialize(data_source)
    broker = DataBroker(db, spec)

    try:
        data = broker.get_data(request_body)
    except requests.exceptions.RequestException as e:
        logger.error(str(e))
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        logger.error(str(e))
        raise HTTPException(status_code=500, detail=str(e))

    return data
