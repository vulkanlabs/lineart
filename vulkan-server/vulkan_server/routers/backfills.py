from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from vulkan.core.run import RunStatus
from vulkan_server import schemas
from vulkan_server.backtest.launcher import get_backtest_job_status
from vulkan_server.backtest.results import ResultsDB, get_results_db
from vulkan_server.db import Backfill, get_db

router = APIRouter(
    prefix="/backfills",
    tags=["backfills"],
    responses={404: {"description": "Not found"}},
)


@router.get("/", response_model=list[schemas.Backfill])
def list_backfills(db=Depends(get_db)):
    results = db.query(Backfill).all()
    if len(results) == 0:
        return Response(status_code=204)
    return results


@router.get("/{backfill_id}", response_model=schemas.Backfill)
def get_backfill(
    backfill_id: str,
    db: Session = Depends(get_db),
):
    backfill = (
        db.query(Backfill)
        .filter_by(
            backfill_id=backfill_id,
        )
        .first()
    )
    if backfill is None:
        return Response(status_code=404)
    return backfill


@router.get("/{backfill_id}/status", response_model=schemas.BackfillStatus)
def get_backfill_status(
    backfill_id: str,
    db: Session = Depends(get_db),
):
    backfill = (
        db.query(Backfill)
        .filter_by(
            backfill_id=backfill_id,
        )
        .first()
    )
    if backfill is None:
        return Response(status_code=404)

    status = get_backtest_job_status(backfill.gcp_job_id)
    return schemas.BackfillStatus(backfill_id=backfill_id, status=status)


@router.put("/{backfill_id}")
def update_backfill(
    backfill_id: str,
    status: RunStatus,
    results_path: str,
    db: Session = Depends(get_db),
):
    backfill = (
        db.query(Backfill)
        .filter_by(
            backfill_id=backfill_id,
        )
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
    db: Session = Depends(get_db),
    results_db: ResultsDB = Depends(get_results_db),
):
    backfill = (
        db.query(Backfill)
        .filter_by(
            backfill_id=backfill_id,
        )
        .first()
    )
    if backfill is None:
        raise HTTPException(
            status_code=404,
            detail={"msg": f"Backtest {backfill_id} not found"},
        )

    if backfill.status != RunStatus.SUCCESS:
        raise HTTPException(
            status_code=400,
            detail={
                "msg": f"Backtest {backfill_id} is not finished yet or finished with a failure"
            },
        )

    try:
        results = results_db.load_data(backfill.output_path)
    except Exception:
        raise HTTPException(
            status_code=500,
            detail={
                "msg": (
                    "Failed to load backfill results. "
                    "This can happen if the backfill is still running or if there is an error."
                )
            },
        )

    return results.to_dict(orient="records")
