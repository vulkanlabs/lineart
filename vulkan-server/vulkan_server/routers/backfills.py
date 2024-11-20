import os

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, Response
from gcsfs import GCSFileSystem
from pyarrow import parquet
from sqlalchemy.orm import Session
from vulkan.core.run import RunStatus

from vulkan_server import schemas
from vulkan_server.auth import get_project_id
from vulkan_server.db import Backfill, get_db
from vulkan_server.logger import init_logger

logger = init_logger("backfills")
router = APIRouter(
    prefix="/backfills",
    tags=["backfills"],
    responses={404: {"description": "Not found"}},
)

GCP_PROJECT_ID = os.environ.get("GCP_PROJECT_ID")
GCP_DATAFLOW_JOB_LOCATION = os.getenv("GCP_DATAFLOW_JOB_LOCATION")


@router.get("/", response_model=list[schemas.Backfill])
def list_backfills(project_id: str = Depends(get_project_id), db=Depends(get_db)):
    results = db.query(Backfill).filter_by(project_id=project_id).all()
    if len(results) == 0:
        return Response(status_code=204)
    return results


@router.get("/{backfill_id}", response_model=schemas.Backfill)
def get_backfill(
    backfill_id: str,
    project_id: str = Depends(get_project_id),
    db: Session = Depends(get_db),
):
    backfill = (
        db.query(Backfill)
        .filter_by(backfill_id=backfill_id, project_id=project_id)
        .first()
    )
    if backfill is None:
        return Response(status_code=404)
    return backfill


@router.put("/{backfill_id}")
def update_backfill(
    backfill_id: str,
    status: RunStatus,
    results_path: str,
    db: Session = Depends(get_db),
    project_id: str = Depends(get_project_id),
):
    backfill = (
        db.query(Backfill)
        .filter_by(backfill_id=backfill_id, project_id=project_id)
        .first()
    )
    if backfill is None:
        return Response(status_code=404)

    backfill.status = status
    backfill.results_path = results_path
    db.commit()
    return backfill


@router.get("/{backfill_id}/results")
def get_backfill_results(
    backfill_id: str,
    project_id: str = Depends(get_project_id),
    db: Session = Depends(get_db),
):
    backfill = (
        db.query(Backfill)
        .filter_by(backfill_id=backfill_id, project_id=project_id)
        .first()
    )
    if backfill is None:
        return Response(status_code=404)
    # FIXME: check also that the status is "SUCCESS"

    try:
        results = _load_backfill_results(str(backfill.output_path))
    except Exception:
        raise HTTPException(
            status_code=500,
            detail={
                "msg": (
                    "Failed to load backtest results. "
                    "This can happen if the backtest is still running or if there is an error."
                )
            },
        )

    return results.to_dict(orient="records")


def _load_backfill_results(results_path: str) -> pd.DataFrame:
    token_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

    logger.info(f"Loading results from {results_path}")

    fs = GCSFileSystem(project=GCP_PROJECT_ID, access="read_write", token=token_path)
    files = fs.ls(results_path)

    if len(files) == 0:
        raise ValueError(f"No files found in {results_path}")

    ds = parquet.ParquetDataset(files, filesystem=fs)
    logger.info(f"Read {len(ds)} records from {results_path}")
    return ds.read().to_pandas()
