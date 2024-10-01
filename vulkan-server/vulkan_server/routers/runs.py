import pickle
from collections import defaultdict
from typing import Annotated

import sqlalchemy
from fastapi import APIRouter, Body, Depends, HTTPException
from sqlalchemy.orm import Session
from vulkan.core.run import RunStatus

from vulkan_server import schemas
from vulkan_server.auth import get_project_id
from vulkan_server.dagster.client import get_dagster_db
from vulkan_server.db import DBSession, Run, StepMetadata, get_db
from vulkan_server.logger import init_logger

logger = init_logger("runs")
router = APIRouter(
    prefix="/runs",
    tags=["runs"],
    responses={404: {"description": "Not found"}},
)


@router.get("/{run_id}/data", response_model=schemas.RunData)
def get_run_data(
    run_id: str,
    db: Session = Depends(get_db),
    project_id: str = Depends(get_project_id),
):
    run = db.query(Run).filter_by(run_id=run_id, project_id=project_id).first()
    if run is None:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")

    dagster_db = get_dagster_db()
    with dagster_db.connect() as conn:
        q = sqlalchemy.text("""
        SELECT step_name, object_name, value 
            FROM objects 
            WHERE run_id = :run_id
        """)
        results = conn.execute(q, {"run_id": run_id}).fetchall()
        if len(results) == 0:
            return {"run_id": run_id, "data": {}}

        # TODO: on a separate query, we can get the step metadata to
        # enrich the results with node type, execution times etc.

        data = defaultdict(dict)
        for result in results:
            step_name, object_name, value = result
            if object_name != "result":
                # This is a branch node output.
                # The object_name represents the path taken.
                data[step_name] = object_name
            else:
                try:
                    value = pickle.loads(value)
                except pickle.UnpicklingError:
                    raise HTTPException(
                        status_code=500,
                        detail=f"Failed to unpickle data for {step_name}.{object_name}",
                    )
                data[step_name] = value

    return {
        "run_id": run_id,
        "last_updated_at": run.last_updated_at,
        "data": data,
        # "metadata": metadata,
    }


# TODO: Add a separate route with inputs and outputs
# This requires leveraging the graph structure to extract the dependencies
# and then get dependency outputs from the run.
# For the outputs, it's the same as the endpoint above.


@router.get("/{run_id}", response_model=schemas.Run)
def get_run(run_id: str, db: Session = Depends(get_db)):
    run = db.query(Run).filter_by(run_id=run_id).first()
    if run is None:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")
    return run


@router.put("/{run_id}", response_model=schemas.Run)
def update_run(
    run_id: str,
    status: Annotated[str, Body()],
    result: Annotated[str, Body()],
    db: Session = Depends(get_db),
):
    run = db.query(Run).filter_by(run_id=run_id).first()
    if run is None:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")

    try:
        status = RunStatus(status)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    run.status = status
    run.result = result
    db.commit()
    return run


@router.post("/{run_id}/metadata")
def publish_metadata(run_id: str, config: schemas.StepMetadataBase):
    try:
        with DBSession() as db:
            args = {"run_id": run_id, **config.model_dump()}
            meta = StepMetadata(**args)
            db.add(meta)
            db.commit()
            return {"status": "success"}
    except KeyError as e:
        raise HTTPException(status_code=400, detail=e)
    except Exception as e:
        raise HTTPException(status_code=500, detail=e)
