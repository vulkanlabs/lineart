import datetime
from typing import Annotated, Any

import pandas as pd
import requests
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func as F
from sqlalchemy import select
from sqlalchemy.orm import Session
from vulkan_public.data_source import DataSourceType
from vulkan_public.schemas import DataSourceSpec

from vulkan_server import schemas
from vulkan_server.data.broker import DataBroker
from vulkan_server.db import (
    DataObject,
    DataSource,
    PolicyDataDependency,
    PolicyVersion,
    RunDataRequest,
    UploadedFile,
    get_db,
)
from vulkan_server.logger import init_logger
from vulkan_server.utils import validate_date_range

logger = init_logger("data")

sources = APIRouter(
    prefix="/data-sources",
    tags=["data-sources"],
    responses={404: {"description": "Not found"}},
)


@sources.get("/", response_model=list[schemas.DataSource])
def list_data_sources(
    include_archived: bool = False,
    db: Session = Depends(get_db),
):
    filters = {}
    if not include_archived:
        filters["archived"] = False

    stmt = select(DataSource).filter_by(**filters)
    data_sources = db.execute(stmt).scalars().all()
    response = [schemas.DataSource.from_orm(ds) for ds in data_sources]
    return response


@sources.post("/")
def create_data_source(
    spec: DataSourceSpec,
    db: Session = Depends(get_db),
):
    ds = (
        db.query(DataSource)
        .filter_by(
            name=spec.name,
        )
        .first()
    )
    if ds is not None:
        raise HTTPException(status_code=400, detail="Data source already exists")

    if spec.source.source_type == DataSourceType.LOCAL_FILE:
        msg = "Local file data sources are not supported for remote execution"
        raise ValueError(msg)
    if spec.source.source_type == DataSourceType.REGISTERED_FILE:
        # Load the file path from DB and add it to the config
        uploaded_file = (
            db.query(UploadedFile)
            .filter_by(uploaded_file_id=spec.source.file_id)
            .first()
        )
        if uploaded_file is None:
            msg = f"Uploaded file {spec.source.file_id} not found"
            raise HTTPException(status_code=400, detail=msg)

        spec.source.path = uploaded_file.file_path

    data_source = DataSource.from_spec(spec)
    db.add(data_source)
    db.commit()

    return {"data_source_id": data_source.data_source_id}


@sources.get("/{data_source_id}", response_model=schemas.DataSource)
def get_data_source(
    data_source_id: str,
    db: Session = Depends(get_db),
):
    data_source = (
        db.query(DataSource)
        .filter_by(
            data_source_id=data_source_id,
        )
        .first()
    )
    if data_source is None:
        raise HTTPException(status_code=404, detail="Data source not found")

    response = schemas.DataSource.from_orm(data_source)
    return response


@sources.delete("/{data_source_id}")
def delete_data_source(
    data_source_id: str,
    db: Session = Depends(get_db),
):
    # TODO: ensure this function can only be executed by ADMIN level users
    data_source = (
        db.query(DataSource)
        .filter_by(
            data_source_id=data_source_id,
            archived=False,
        )
        .first()
    )
    if data_source is None:
        msg = f"Tried to delete non-existent data source {data_source_id}"
        raise HTTPException(status_code=404, detail=msg)

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


@sources.get(
    "/{data_source_id}/objects", response_model=list[schemas.DataObjectMetadata]
)
def list_data_objects(
    data_source_id: str,
    db: Session = Depends(get_db),
):
    data_source = (
        db.query(DataSource)
        .filter_by(
            data_source_id=data_source_id,
        )
        .first()
    )
    if data_source is None:
        raise HTTPException(status_code=404, detail="Data source not found")

    data_objects = db.query(DataObject).filter_by(data_source_id=data_source_id).all()
    return [
        schemas.DataObjectMetadata(
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
    db: Session = Depends(get_db),
):
    data_object = (
        db.query(DataObject)
        .filter_by(
            data_source_id=data_source_id,
            data_object_id=data_object_id,
        )
        .first()
    )
    if data_object is None:
        raise HTTPException(status_code=404, detail="Data object not found")

    return data_object


@sources.get("/{data_source_id}/stats", response_model=list[Any])
def get_request_stats(
    data_source_id: str,
    start_date: Annotated[datetime.date | None, Query()] = None,
    end_date: Annotated[datetime.date | None, Query()] = None,
    db: Session = Depends(get_db),
):
    start_date, end_date = validate_date_range(start_date, end_date)

    date_clause = F.DATE(RunDataRequest.created_at).label("date")

    q = (
        select(
            date_clause,
            RunDataRequest.data_origin.label("origin"),
            F.count(RunDataRequest.run_data_request_id).label("count"),
        )
        .where(
            (RunDataRequest.data_source_id == data_source_id)
            & (RunDataRequest.created_at >= start_date)
            & (F.DATE(RunDataRequest.created_at) <= end_date)
        )
        .group_by(date_clause, RunDataRequest.data_origin)
    )
    df = pd.read_sql(q, db.bind).fillna(0)
    return df.to_dict(orient="records")


broker = APIRouter(
    prefix="/data-broker",
    tags=["data-broker"],
    responses={404: {"description": "Not found"}},
)


@broker.post("/", response_model=schemas.DataBrokerResponse)
def request_data_from_broker(
    request: schemas.DataBrokerRequest,
    db: Session = Depends(get_db),
):
    # TODO: Control access to the data source by project_id
    data_source = db.query(DataSource).filter_by(name=request.data_source_name).first()
    if data_source is None:
        raise HTTPException(status_code=404, detail="Data source not found")

    spec = schemas.DataSource.from_orm(data_source)
    broker = DataBroker(db, spec)

    try:
        data = broker.get_data(request.request_body, request.variables)
        request_obj = RunDataRequest(
            run_id=request.run_id,
            data_object_id=data.data_object_id,
            data_source_id=spec.data_source_id,
            data_origin=data.origin,
        )
        db.add(request_obj)
        db.commit()
    except requests.exceptions.RequestException as e:
        logger.error(str(e))
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        logger.error(str(e))
        raise HTTPException(status_code=500, detail=str(e))

    return data
