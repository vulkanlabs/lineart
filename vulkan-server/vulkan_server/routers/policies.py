import datetime
from typing import Annotated, Any

import pandas as pd
import sqlalchemy.exc
from fastapi import APIRouter, Body, Depends, HTTPException, Query, Response
from sqlalchemy import func as F
from sqlalchemy import select
from sqlalchemy.orm import Session

from vulkan.core.run import RunStatus
from vulkan_server import schemas
from vulkan_server.dagster.launch_run import (
    DagsterRunLauncher,
    allocate_runs,
    get_dagster_launcher,
)
from vulkan_server.db import (
    Policy,
    PolicyVersion,
    PolicyVersionStatus,
    Run,
    RunGroup,
    get_db,
)
from vulkan_server.events import VulkanEvent
from vulkan_server.logger import VulkanLogger, get_logger
from vulkan_server.utils import validate_date_range

router = APIRouter(
    prefix="/policies",
    tags=["policies"],
    responses={404: {"description": "Not found"}},
)


@router.get("/", response_model=list[schemas.Policy])
def list_policies(
    include_archived: bool = False,
    db: Session = Depends(get_db),
):
    filters = dict()
    if not include_archived:
        filters["archived"] = False

    policies = db.query(Policy).filter_by(**filters).all()
    if len(policies) == 0:
        return Response(status_code=204)
    return policies


@router.post("/", response_model=schemas.Policy)
def create_policy(
    config: schemas.PolicyCreate,
    logger: VulkanLogger = Depends(get_logger),
    db: Session = Depends(get_db),
):
    policy = Policy(**config.model_dump())
    db.add(policy)
    db.commit()
    logger.event(
        VulkanEvent.POLICY_CREATED, policy_id=policy.policy_id, **config.model_dump()
    )
    return policy


@router.get("/{policy_id}", response_model=schemas.Policy)
def get_policy(
    policy_id: str,
    db: Session = Depends(get_db),
):
    policy = (
        db.query(Policy)
        .filter_by(
            policy_id=policy_id,
        )
        .first()
    )
    if policy is None:
        return Response(status_code=404)
    return policy


@router.put("/{policy_id}", response_model=schemas.Policy)
def update_policy(
    policy_id: str,
    config: schemas.PolicyBase,
    logger: VulkanLogger = Depends(get_logger),
    db: Session = Depends(get_db),
):
    policy = (
        db.query(Policy)
        .filter_by(
            policy_id=policy_id,
        )
        .first()
    )
    if policy is None:
        msg = f"Tried to update non-existent policy {policy_id}"
        raise HTTPException(status_code=404, detail=msg)

    allocation_strategy = _validate_allocation_strategy(
        db=db,
        allocation_strategy=config.allocation_strategy,
    )
    policy.allocation_strategy = allocation_strategy.model_dump()

    if config.name is not None and config.name != policy.name:
        policy.name = config.name
    if config.description is not None and config.description != policy.description:
        policy.description = config.description

    db.commit()
    logger.event(VulkanEvent.POLICY_UPDATED, policy_id=policy_id, **config.model_dump())
    return policy


def _validate_allocation_strategy(db, allocation_strategy):
    if allocation_strategy is None:
        return None

    if len(allocation_strategy.choice) == 0:
        raise HTTPException(
            status_code=400,
            detail="Allocation strategy must have at least one option",
        )

    total_frequency = sum([option.frequency for option in allocation_strategy.choice])
    if total_frequency != 1000:
        raise HTTPException(
            status_code=400,
            detail="The sum of frequencies must be 1000",
        )

    schemas = []

    if allocation_strategy.shadow is not None:
        for policy_version_id in allocation_strategy.shadow:
            version = _validate_policy_version(db, policy_version_id)
            schemas.append(version.input_schema)

    for option in allocation_strategy.choice:
        version = _validate_policy_version(db, option.policy_version_id)
        schemas.append(version.input_schema)

    # TODO: Validate if schemas are compatible
    # TODO: Validate if config_variables are compatible

    return allocation_strategy


def _validate_policy_version(db, policy_version_id):
    policy_version = (
        db.query(PolicyVersion).filter_by(policy_version_id=policy_version_id).first()
    )
    if policy_version is None:
        msg = f"Tried to use non-existent version {policy_version_id}"
        raise HTTPException(status_code=404, detail=msg)

    if policy_version.status != PolicyVersionStatus.VALID:
        msg = f"Tried to use invalid version {policy_version_id}"
        raise HTTPException(status_code=400, detail=msg)

    return policy_version


@router.delete("/{policy_id}")
def delete_policy(
    policy_id: str,
    logger: VulkanLogger = Depends(get_logger),
    db: Session = Depends(get_db),
):
    policy = (
        db.query(Policy)
        .filter_by(
            policy_id=policy_id,
        )
        .first()
    )
    if policy is None or policy.archived:
        msg = f"Tried to delete non-existent policy {policy_id}"
        raise HTTPException(status_code=404, detail=msg)

    policy_versions = (
        db.query(PolicyVersion)
        .filter_by(
            policy_id=policy_id,
            archived=False,
        )
        .all()
    )
    if len(policy_versions) > 0:
        msg = f"Policy {policy_id} has associated versions, delete them first"
        raise HTTPException(status_code=400, detail=msg)

    policy.archived = True
    db.commit()
    logger.event(VulkanEvent.POLICY_DELETED, policy_id=policy_id)
    return {"policy_id": policy_id}


@router.get(
    "/{policy_id}/versions",
    response_model=list[schemas.PolicyVersion],
)
def list_policy_versions(
    policy_id: str,
    include_archived: bool = False,
    db: Session = Depends(get_db),
):
    filters = dict(
        policy_id=policy_id,
    )
    if not include_archived:
        filters["archived"] = False

    policy_versions = (
        db.query(PolicyVersion)
        .filter_by(**filters)
        .order_by(PolicyVersion.created_at.asc())
        .all()
    )
    if len(policy_versions) == 0:
        return Response(status_code=204)
    return policy_versions


@router.get("/{policy_id}/runs", response_model=list[schemas.Run])
def list_runs_by_policy(
    policy_id: str,
    start_date: datetime.date | None = None,
    end_date: datetime.date | None = None,
    db: Session = Depends(get_db),
):
    start_date, end_date = validate_date_range(start_date, end_date)
    q = (
        select(Run)
        .join(PolicyVersion)
        .filter(
            (PolicyVersion.policy_id == policy_id)
            & (Run.created_at >= start_date)
            & (F.DATE(Run.created_at) <= end_date)
        )
        .order_by(Run.created_at.desc())
    )
    runs = db.execute(q).scalars().all()
    if len(runs) == 0:
        return Response(status_code=204)
    return runs


@router.post("/{policy_id}/runs")
def create_run_group(
    policy_id: str,
    input_data: Annotated[dict, Body()],
    config_variables: Annotated[dict, Body(default_factory=list)],
    logger: VulkanLogger = Depends(get_logger),
    db: Session = Depends(get_db),
    launcher: DagsterRunLauncher = Depends(get_dagster_launcher),
):
    try:
        policy = (
            db.query(Policy)
            .filter_by(
                policy_id=policy_id,
            )
            .first()
        )
    except sqlalchemy.exc.DataError:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "UNHANDLED_EXCEPTION",
                "msg": f"Invalid policy_id: {policy_id}",
            },
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error": "UNHANDLED_EXCEPTION",
                "msg": f"Failed to get policy: {str(e)}",
            },
        )

    if policy is None:
        raise HTTPException(status_code=404, detail=f"Policy {policy_id} not found")

    if policy.allocation_strategy is None:
        raise HTTPException(
            status_code=400,
            detail=f"Policy {policy_id} has no allocation strategy",
        )

    run_group = RunGroup(
        policy_id=policy_id,
        input_data=input_data,
    )
    db.add(run_group)
    db.commit()

    strategy = schemas.PolicyAllocationStrategy.model_validate(
        policy.allocation_strategy
    )
    logger.system.info(
        f"Allocating runs with input_data {input_data}",
        extra={"extra": {"policy_id": policy_id}},
    )

    runs = allocate_runs(
        db=db,
        launcher=launcher,
        input_data=input_data,
        run_group_id=run_group.run_group_id,
        allocation_strategy=strategy,
    )
    return {
        "policy_id": policy.policy_id,
        "run_group_id": run_group.run_group_id,
        "runs": runs,
    }


@router.post("/{policy_id}/runs/duration", response_model=list[Any])
def run_duration_stats_by_policy(
    policy_id: str,
    start_date: datetime.date | None = None,
    end_date: datetime.date | None = None,
    versions: Annotated[list[str] | None, Body(embed=True)] = None,
    db: Session = Depends(get_db),
):
    start_date, end_date = validate_date_range(start_date, end_date)
    if versions is None:
        versions = select(PolicyVersion.policy_version_id).where(
            PolicyVersion.policy_id == policy_id
        )

    duration_seconds = F.extract("epoch", Run.last_updated_at - Run.created_at)
    date_clause = F.DATE(Run.created_at).label("date")

    q = (
        select(
            date_clause,
            F.avg(duration_seconds).label("avg_duration"),
            F.min(duration_seconds).label("min_duration"),
            F.max(duration_seconds).label("max_duration"),
        )
        .where(
            (Run.policy_version_id.in_(versions))
            & (Run.created_at >= start_date)
            & (F.DATE(Run.created_at) <= end_date)
        )
        .group_by(date_clause)
    )
    df = pd.read_sql(q, db.bind)

    return df.to_dict(orient="records")


@router.post("/{policy_id}/runs/duration/by_status", response_model=list[Any])
def run_duration_stats_by_policy_status(
    policy_id: str,
    start_date: datetime.date | None = None,
    end_date: datetime.date | None = None,
    versions: Annotated[list[str] | None, Body(embed=True)] = None,
    db: Session = Depends(get_db),
):
    start_date, end_date = validate_date_range(start_date, end_date)

    duration_seconds = F.extract("epoch", Run.last_updated_at - Run.created_at)
    date_clause = F.DATE(Run.created_at).label("date")

    if versions is None:
        versions = select(PolicyVersion.policy_version_id).where(
            PolicyVersion.policy_id == policy_id
        )
    query = (
        select(
            date_clause,
            Run.status,
            F.avg(duration_seconds).label("avg_duration"),
        )
        .where(
            (Run.policy_version_id.in_(versions))
            & (Run.created_at >= start_date)
            & (F.DATE(Run.created_at) <= end_date)
        )
        .group_by(date_clause, Run.status)
    )
    df = pd.read_sql(query, db.bind)
    df = df.pivot(
        index=date_clause.name, values="avg_duration", columns=["status"]
    ).reset_index()
    return df.to_dict(orient="records")


@router.post("/{policy_id}/runs/count", response_model=list[Any])
def runs_by_policy(
    policy_id: str,
    start_date: datetime.date | None = None,
    end_date: datetime.date | None = None,
    versions: Annotated[list[str] | None, Body(embed=True)] = None,
    db: Session = Depends(get_db),
):
    start_date, end_date = validate_date_range(start_date, end_date)
    if versions is None:
        versions = select(PolicyVersion.policy_version_id).where(
            PolicyVersion.policy_id == policy_id
        )

    date_clause = F.DATE(Run.created_at).label("date")
    q = (
        select(
            date_clause,
            F.count(Run.run_id).label("count"),
            (
                100
                * F.count(Run.run_id).filter(Run.status == RunStatus.FAILURE)
                / F.count(Run.run_id)
            ).label("error_rate"),
        )
        .where(
            (Run.policy_version_id.in_(versions))
            & (Run.created_at >= start_date)
            & (F.DATE(Run.created_at) <= end_date)
        )
        .group_by(date_clause)
    )
    df = pd.read_sql(q, db.bind)
    return df.to_dict(orient="records")


@router.post("/{policy_id}/runs/outcomes", response_model=list[Any])
def runs_outcomes_by_policy(
    policy_id: str,
    start_date: Annotated[datetime.date | None, Query()] = None,
    end_date: Annotated[datetime.date | None, Query()] = None,
    versions: Annotated[list[str] | None, Body(embed=True)] = None,
    db: Session = Depends(get_db),
):
    start_date, end_date = validate_date_range(start_date, end_date)

    if versions is None:
        versions = select(PolicyVersion.policy_version_id).where(
            PolicyVersion.policy_id == policy_id
        )

    date_clause = F.DATE(Run.created_at).label("date")
    subquery = (
        select(date_clause, F.count(Run.run_id).label("total"))
        .where(
            (Run.policy_version_id.in_(versions))
            & (Run.created_at >= start_date)
            & (F.DATE(Run.created_at) <= end_date)
        )
        .group_by(date_clause)
        .subquery()
    )

    q = (
        select(
            date_clause,
            Run.result.label("result"),
            F.count(Run.run_id).label("count"),
            subquery.c.total.label("total"),
        )
        .join(subquery, onclause=subquery.c.date == date_clause)
        .where(
            (Run.policy_version_id.in_(versions))
            & (Run.created_at >= start_date)
            & (F.DATE(Run.created_at) <= end_date)
        )
        .group_by(date_clause, Run.result, subquery.c.total)
    )
    df = pd.read_sql(q, db.bind)
    df["percentage"] = 100 * df["count"] / df["total"]
    df = (
        df.pivot(
            index=date_clause.name, values=["count", "percentage"], columns=["result"]
        )
        .reset_index()
        .fillna(0)
    )
    return df.to_dict(orient="records")
