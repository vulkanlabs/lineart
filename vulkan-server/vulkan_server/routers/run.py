from typing import Annotated

from fastapi import APIRouter, Body, Depends, HTTPException
from sqlalchemy.orm import Session
from vulkan.core.run import RunStatus

from vulkan_server import schemas
from vulkan_server.db import DBSession, Run, StepMetadata, get_db
from vulkan_server.logger import init_logger

logger = init_logger("policies")
router = APIRouter(
    prefix="/runs",
    tags=["runs"],
    responses={404: {"description": "Not found"}},
)


@router.get("/{run_id}", response_model=schemas.Run)
def get_run(run_id: int, db: Session = Depends(get_db)):
    run = db.query(Run).filter_by(run_id=run_id).first()
    if run is None:
        raise HTTPException(status_code=400, detail=f"Run {run_id} not found")
    return run


@router.put("/{run_id}", response_model=schemas.Run)
def update_run(
    run_id: int,
    status: Annotated[str, Body()],
    result: Annotated[str, Body()],
    db: Session = Depends(get_db),
):
    run = db.query(Run).filter_by(run_id=run_id).first()
    if run is None:
        raise HTTPException(status_code=400, detail=f"Run {run_id} not found")

    try:
        status = RunStatus(status)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    run.status = status
    run.result = result
    db.commit()
    return run


@router.post("/{run_id}/metadata")
def publish_metadata(run_id: int, config: schemas.StepMetadataBase):
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
