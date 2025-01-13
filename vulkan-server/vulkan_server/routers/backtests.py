from typing import Annotated

import pandas as pd
from fastapi import APIRouter, Body, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from vulkan.core.run import JobStatus
from vulkan_server import schemas
from vulkan_server.auth import get_project_id
from vulkan_server.backtest.backtest import ensure_beam_workspace, resolve_backtest_envs
from vulkan_server.backtest.launcher import BacktestLauncher, get_launcher
from vulkan_server.backtest.results import ResultsDB, get_results_db
from vulkan_server.config_variables import _get_policy_version_defaults
from vulkan_server.db import (
    Backfill,
    Backtest,
    BacktestMetrics,
    BeamWorkspace,
    PolicyVersion,
    UploadedFile,
    get_db,
)
from vulkan_server.logger import init_logger

logger = init_logger("backtests")
router = APIRouter(
    prefix="/backtests",
    tags=["backtests"],
    responses={404: {"description": "Not found"}},
)


@router.get("/", response_model=list[schemas.Backtest])
def list_backtests(
    policy_version_id: str | None = None,
    project_id: str = Depends(get_project_id),
    db=Depends(get_db),
):
    filters = dict(project_id=project_id)
    if policy_version_id is not None:
        filters["policy_version_id"] = policy_version_id

    backtests = db.query(Backtest).filter_by(**filters).all()
    if len(backtests) == 0:
        return Response(status_code=204)
    return backtests


# FIXME: if config variables is an empty list, no runs are created!
@router.post("/", response_model=schemas.Backtest)
def launch_backtest(
    policy_version_id: Annotated[str, Body()],
    input_file_id: Annotated[str, Body()],
    config_variables: Annotated[list[dict] | None, Body()],
    metrics_config: Annotated[schemas.BacktestMetricsConfig | None, Body()] = None,
    db: Session = Depends(get_db),
    project_id: str = Depends(get_project_id),
    run_launcher: BacktestLauncher = Depends(get_launcher),
):
    policy_version = (
        db.query(PolicyVersion)
        .filter_by(project_id=project_id, policy_version_id=policy_version_id)
        .first()
    )
    if policy_version is None:
        raise HTTPException(
            status_code=404,
            detail={"msg": f"Policy Version {policy_version_id} not found"},
        )

    try:
        workspace: BeamWorkspace = ensure_beam_workspace(policy_version_id, db)
    except Exception as e:
        logger.error(f"Backtest launch failed: {e}")
        raise HTTPException(
            status_code=400,
            detail={"msg": str(e)},
        )

    input_file = (
        db.query(UploadedFile)
        .filter_by(
            project_id=project_id,
            uploaded_file_id=input_file_id,
        )
        .first()
    )
    if input_file is None:
        raise HTTPException(
            status_code=404,
            detail={"msg": f"Input File {input_file_id} not found"},
        )

    # Resolve Config Variables
    if config_variables is not None:
        policy_version_defaults = _get_policy_version_defaults(
            db=db,
            policy_version_id=policy_version_id,
            required_variables=policy_version.variables,
        )
        try:
            resolved_envs = resolve_backtest_envs(
                environments=config_variables,
                policy_version_defaults=policy_version_defaults,
                required_variables=policy_version.variables,
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail={"msg": str(e)})
        except Exception as e:
            raise HTTPException(status_code=500, detail={"msg": str(e)})
    else:
        # No config variables provided, use defaults.
        resolved_envs = [{}]

    backtest = Backtest(
        project_id=project_id,
        policy_version_id=policy_version_id,
        input_file_id=input_file_id,
        environments=resolved_envs,
        status=JobStatus.PENDING,
    )
    if metrics_config is not None:
        backtest.calculate_metrics = True
        backtest.target_column = metrics_config.target_column
        backtest.time_column = metrics_config.time_column
        backtest.group_by_columns = metrics_config.group_by_columns
    db.add(backtest)
    db.commit()

    N = len(resolved_envs)
    for i, env in enumerate(resolved_envs, start=1):
        logger.debug(f"Launching backfill ({i / N})")
        backfill = run_launcher.create_backfill(
            project_id=project_id,
            backtest_id=backtest.backtest_id,
            workspace=workspace,
            policy_version=policy_version,
            input_data_path=input_file.file_path,
            resolved_config_variables=env,
        )
        logger.debug(f"Launched backfill ({i / N}): {backfill.backfill_id}")

    return backtest


@router.get("/{backtest_id}/", response_model=schemas.Backtest)
def get_backtest(
    backtest_id: str,
    project_id: str = Depends(get_project_id),
    db: Session = Depends(get_db),
):
    backtest = (
        db.query(Backtest)
        .filter_by(backtest_id=backtest_id, project_id=project_id)
        .first()
    )
    if backtest is None:
        raise HTTPException(
            status_code=404,
            detail={"msg": f"Backtest {backtest_id} not found"},
        )

    return backtest


@router.get("/{backtest_id}/status", response_model=schemas.BacktestStatus)
def get_backtest_status(
    backtest_id: str,
    project_id: str = Depends(get_project_id),
    db: Session = Depends(get_db),
):
    backtest = (
        db.query(Backtest)
        .filter_by(backtest_id=backtest_id, project_id=project_id)
        .first()
    )
    if backtest is None:
        raise HTTPException(
            status_code=404,
            detail={"msg": f"Backtest {backtest_id} not found"},
        )

    backfills = (
        db.query(Backfill)
        .filter_by(backtest_id=backtest_id, project_id=project_id)
        .all()
    )
    if len(backfills) == 0:
        raise HTTPException(
            status_code=404,
            detail={"msg": f"No backfills found for backtest {backtest_id}"},
        )

    backfill_status = [
        schemas.BackfillStatus(
            backfill_id=b.backfill_id,
            status=b.status,
            config_variables=b.config_variables,
        )
        for b in backfills
    ]
    return {
        "backtest_id": backtest_id,
        "status": backtest.status,
        "backfills": backfill_status,
    }


def launch_metrics_job(
    backtest_id: str,
    db: Session,
    launcher: BacktestLauncher,
):
    backtest = db.query(Backtest).filter_by(backtest_id=backtest_id).first()
    if backtest is None:
        raise HTTPException(
            status_code=404, detail={"msg": f"Backtest {backtest_id} not found"}
        )

    existing_metrics_job = (
        db.query(BacktestMetrics).filter_by(backtest_id=backtest_id).first()
    )
    if existing_metrics_job is not None:
        logger.debug(f"SKIPPING: Metrics job already exists for backtest {backtest_id}")
        return existing_metrics_job

    input_file = (
        db.query(UploadedFile)
        .filter_by(uploaded_file_id=backtest.input_file_id)
        .first()
    )

    # Attention: This may be specific to GCS, we still need to validate for other FS
    results_path = f"{launcher.backtest_output_path(backtest.project_id, backtest_id)}/backfills/**"

    metrics = launcher.create_metrics(
        backtest_id=backtest_id,
        project_id=str(backtest.project_id),
        input_data_path=input_file.file_path,
        results_data_path=results_path,
        target_column=backtest.target_column,
        time_column=backtest.time_column,
        group_by_columns=backtest.group_by_columns,
    )
    return metrics


@router.get("/{backtest_id}/metrics", response_model=schemas.BacktestMetrics)
def get_metrics_job(
    backtest_id: str,
    project_id=Depends(get_project_id),
    db=Depends(get_db),
):
    backtest = (
        db.query(Backtest)
        .filter_by(backtest_id=backtest_id, project_id=project_id)
        .first()
    )
    if backtest is None:
        raise HTTPException(
            status_code=404, detail={"msg": f"Backtest {backtest_id} not found"}
        )

    metrics_job = (
        db.query(BacktestMetrics)
        .filter_by(backtest_id=backtest_id, project_id=project_id)
        .first()
    )
    if metrics_job is None:
        raise HTTPException(
            status_code=404,
            detail={"msg": f"Metrics job not found for backtest {backtest_id}"},
        )

    return metrics_job


@router.get("/{backtest_id}/results")
def get_backtest_results(
    backtest_id: str,
    project_id: str = Depends(get_project_id),
    db: Session = Depends(get_db),
    results_db: ResultsDB = Depends(get_results_db),
):
    backtest = (
        db.query(Backtest)
        .filter_by(backtest_id=backtest_id, project_id=project_id)
        .first()
    )
    if backtest is None:
        raise HTTPException(
            status_code=404,
            detail={"msg": f"Backtest {backtest_id} not found"},
        )
    if backtest.status != JobStatus.DONE:
        raise HTTPException(
            status_code=400,
            detail={"msg": "Backtest is not completed yet"},
        )

    backfills = (
        db.query(Backfill)
        .filter_by(backtest_id=backtest_id, project_id=project_id)
        .all()
    )

    data_paths = [job.output_path for job in backfills]
    logger.info(f"Loading backtest results: {data_paths}")
    try:
        results = results_db.load_data(data_paths)
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


@router.get("/{backtest_id}/metrics/data")
def get_backtest_metrics(
    backtest_id: str,
    target: bool = False,
    time: bool = False,
    column: str | None = None,
    project_id: str = Depends(get_project_id),
    db: Session = Depends(get_db),
):
    backtest = (
        db.query(Backtest)
        .filter_by(backtest_id=backtest_id, project_id=project_id)
        .first()
    )
    if backtest is None:
        raise HTTPException(
            status_code=404, detail={"msg": f"Backtest {backtest_id} not found"}
        )

    backtest_metrics = (
        db.query(BacktestMetrics)
        .filter_by(backtest_id=backtest_id, project_id=project_id)
        .first()
    )
    if backtest_metrics is None:
        raise HTTPException(
            status_code=404,
            detail={"msg": f"Metrics job not found for backtest {backtest_id}"},
        )

    metrics = pd.DataFrame(backtest_metrics.metrics)
    metrics["backfill"] = metrics.backfill_id.apply(lambda x: x[:8])
    agg_columns = ["backfill", "status"]
    num_columns = ["count"]

    if target:
        if backtest.target_column is None:
            raise HTTPException(
                status_code=400,
                detail={"msg": "Target column not specified for backtest"},
            )
        num_columns.extend(["ones", "zeros"])

    if time:
        if backtest.time_column is None:
            raise HTTPException(
                status_code=400,
                detail={"msg": "Time column not specified for backtest"},
            )
        agg_columns.append(backtest.time_column)

    if column is not None:
        if backtest.group_by_columns is None:
            raise HTTPException(
                status_code=400,
                detail={"msg": "Group by columns not specified for backtest"},
            )
        if column not in backtest.group_by_columns:
            raise HTTPException(
                status_code=400,
                detail={"msg": f"Column {column} not in group by columns"},
            )
        agg_columns.append(column)

    data = metrics.groupby(agg_columns)[num_columns].sum().reset_index()
    return data.to_dict(orient="records")
