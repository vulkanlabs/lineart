import pickle
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Body, Depends, HTTPException
from sqlalchemy.orm import Session

from vulkan.core.run import RunStatus
from vulkan_server import schemas
from vulkan_server.dagster.client import DagsterDataClient
from vulkan_server.dagster.launch_run import DagsterRunLauncher, get_dagster_launcher
from vulkan_server.db import Run, RunGroup, StepMetadata, get_db
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
):
    run = db.query(Run).filter_by(run_id=run_id).first()
    if run is None:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")

    run_data = {
        "run_id": run_id,
        "policy_version_id": run.policy_version_id,
        "status": run.status,
        "last_updated_at": run.last_updated_at,
        "steps": {},
    }

    dagster_data_client = DagsterDataClient()
    results = dagster_data_client.get_run_data(run_id)
    if len(results) == 0:
        return run_data

    steps = db.query(StepMetadata).filter_by(run_id=run_id).all()
    if len(steps) == 0:
        return run_data

    results_by_name = {result[0]: (result[1], result[2]) for result in results}
    metadata = {
        step.step_name: {
            "step_name": step.step_name,
            "node_type": step.node_type,
            "start_time": step.start_time,
            "end_time": step.end_time,
            "error": step.error,
            "extra": step.extra,
        }
        for step in steps
    }
    # Parse step data taking metadata into context
    for step_name, step_metadata in metadata.items():
        value = None

        if step_name in results_by_name:
            object_name, value = results_by_name[step_name]
            if object_name != "result":
                # This is a branch node output.
                # The object_name represents the path taken.
                value = object_name
            else:
                try:
                    value = pickle.loads(value)
                except pickle.UnpicklingError:
                    raise HTTPException(
                        status_code=500,
                        detail=f"Failed to unpickle data for {step_name}.{object_name}",
                    )

        run_data["steps"][step_name] = {"output": value, "metadata": step_metadata}

    return run_data


# TODO: Add a separate route with inputs and outputs
# This requires leveraging the graph structure to extract the dependencies
# and then get dependency outputs from the run.
# For the outputs, it's the same as the endpoint above.

# TODO: We should find a way to authenticate the endpoints below


@router.get("/{run_id}/logs", response_model=schemas.RunLogs)
def get_run_logs(run_id: str, db: Session = Depends(get_db)):
    run = db.query(Run).filter_by(run_id=run_id).first()
    if run is None:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")

    dagster_data_client = DagsterDataClient()
    logs = dagster_data_client.get_run_logs(run.dagster_run_id)
    return {
        "run_id": run_id,
        "status": run.status,
        "last_updated_at": run.last_updated_at,
        "logs": logs,
    }


@router.get("/{run_id}", response_model=schemas.Run)
def get_run(run_id: str, db: Session = Depends(get_db)):
    run = db.query(Run).filter_by(run_id=run_id).first()
    if run is None:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")
    return run


@router.post("/{run_id}/metadata")
def publish_metadata(
    run_id: str,
    config: schemas.StepMetadataBase,
    db: Session = Depends(get_db),
):
    try:
        args = {"run_id": run_id, **config.model_dump()}
        meta = StepMetadata(**args)
        db.add(meta)
        db.commit()
        return {"status": "success"}
    except KeyError as e:
        raise HTTPException(status_code=400, detail=e)
    except Exception as e:
        raise HTTPException(status_code=500, detail=e)


@router.put("/{run_id}", response_model=schemas.Run)
def update_run(
    run_id: str,
    status: Annotated[str, Body()],
    result: Annotated[str, Body()],
    metadata: Annotated[dict[str, Any] | None, Body()] = None,
    db: Session = Depends(get_db),
    launcher: DagsterRunLauncher = Depends(get_dagster_launcher),
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
    run.run_metadata = metadata
    db.commit()

    logger.info(f"Run group_id {run.run_group_id}")

    if run.run_group_id is None:
        return run

    # TODO: What to do when the main run fails?
    # TODO: Should we trigger the remaining runs with a subprocess (so we don't
    # halt the API's response)?
    logger.info(f"Launching shadow runs from group {run.run_group_id}")
    _trigger_pending_runs(
        db=db,
        launcher=launcher,
        run_group_id=run.run_group_id,
    )

    return run


def _trigger_pending_runs(
    db: Session,
    launcher: DagsterRunLauncher,
    run_group_id: UUID,
):
    run_group = db.query(RunGroup).filter_by(run_group_id=run_group_id).first()
    input_data = run_group.input_data

    pending_runs = (
        db.query(Run)
        .filter_by(run_group_id=run_group_id, status=RunStatus.PENDING)
        .all()
    )

    # TODO: We're launching all pending runs at once. Should we wait for one to
    # finish before launching the next?
    for run in pending_runs:
        logger.info(f"Launching run {run.run_id}")
        try:
            run = launcher.launch_run(run=run, input_data=input_data)
        except Exception as e:
            # TODO: Structure log to trace the run that failed and the way it was triggered
            logger.error(f"Failed to launch run {run.run_id}: {e}")
            continue
