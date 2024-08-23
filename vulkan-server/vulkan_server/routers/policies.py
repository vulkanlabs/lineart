import datetime
import json
from typing import Annotated, Any

import pandas as pd
from fastapi import APIRouter, Body, Depends, HTTPException, Response
from sqlalchemy import func as F
from sqlalchemy.orm import Session

from vulkan_server import definitions, schemas
from vulkan_server.dagster.client import get_dagster_client
from vulkan_server.dagster.launch_run import launch_run
from vulkan_server.db import (
    DBSession,
    Policy,
    PolicyVersion,
    PolicyVersionStatus,
    Run,
    get_db,
)
from vulkan_server.logger import init_logger

logger = init_logger("policies")
router = APIRouter(
    prefix="/policies",
    tags=["policies"],
    responses={404: {"description": "Not found"}},
)


@router.get("/", response_model=list[schemas.Policy])
def list_policies(db: Session = Depends(get_db)):
    policies = db.query(Policy).all()
    if len(policies) == 0:
        return Response(status_code=204)
    return policies


@router.post("/")
def create_policy(config: schemas.PolicyBase):
    with DBSession() as db:
        policy = Policy(**config.model_dump())
        db.add(policy)
        db.commit()
        logger.info(f"Policy {config.name} created")
        return {"policy_id": policy.policy_id, "name": policy.name}


@router.get("/{policy_id}", response_model=schemas.Policy)
def get_policy(policy_id, db: Session = Depends(get_db)):
    policy = db.query(Policy).filter_by(policy_id=policy_id).first()
    if policy is None:
        return Response(status_code=204)
    return policy


@router.put("/{policy_id}")
def update_policy(
    policy_id: int,
    config: schemas.PolicyUpdate,
):
    with DBSession() as db:
        policy = db.query(Policy).filter_by(policy_id=policy_id).first()
        if policy is None:
            msg = f"Tried to update non-existent policy {policy_id}"
            raise HTTPException(status_code=400, detail=msg)

        if (
            config.active_policy_version_id is not None
            and config.active_policy_version_id != policy.active_policy_version_id
        ):
            policy_version = (
                db.query(PolicyVersion)
                .filter_by(policy_version_id=config.active_policy_version_id)
                .first()
            )
            if policy_version is None:
                msg = f"Tried to use non-existent version {config.active_policy_version_id} for policy {policy_id}"
                raise HTTPException(status_code=400, detail=msg)

            if policy_version.status != PolicyVersionStatus.VALID:
                msg = f"Tried to use invalid version {config.active_policy_version_id} for policy {policy_id}"
                raise HTTPException(status_code=400, detail=msg)

            policy.active_policy_version_id = config.active_policy_version_id

        if config.name is not None and config.name != policy.name:
            policy.name = config.name
        if config.description is not None and config.description != policy.description:
            policy.description = config.description

        db.commit()
        msg = f"Policy {policy_id} updated: active version set to {config.active_policy_version_id}"
        logger.info(msg)
        return {
            "policy_id": policy.policy_id,
            "active_policy_version_id": policy.active_policy_version_id,
        }


@router.get(
    "/{policy_id}/versions",
    response_model=list[schemas.PolicyVersion],
)
def list_policy_versions(policy_id: int, db: Session = Depends(get_db)):
    policy_versions = db.query(PolicyVersion).filter_by(policy_id=policy_id).all()
    if len(policy_versions) == 0:
        return Response(status_code=204)
    return policy_versions


@router.get("/{policy_id}/runs", response_model=list[schemas.Run])
def list_runs_by_policy(policy_id: int, db: Session = Depends(get_db)):
    policy_versions = db.query(PolicyVersion).filter_by(policy_id=policy_id).all()
    policy_version_ids = [v.policy_version_id for v in policy_versions]
    runs = db.query(Run).filter(Run.policy_version_id.in_(policy_version_ids)).all()
    if len(runs) == 0:
        return Response(status_code=204)
    return runs


@router.get("/{policy_id}/runs/count", response_model=list[Any])
def count_runs_by_policy(
    policy_id: int,
    start_date: datetime.date | None = None,
    end_date: datetime.date | None = None,
    group_by_status: bool = False,
    db: Session = Depends(get_db),
):
    if end_date is None:
        end_date = datetime.date.today()
    if start_date is None:
        start_date = end_date - datetime.timedelta(days=30)

    active_version = db.query(Policy).filter_by(policy_id=policy_id).first()
    if active_version is None:
        raise HTTPException(status_code=400, detail=f"Policy {policy_id} not found")

    date_clause = F.DATE(Run.created_at).label("date")
    groupers = []
    if group_by_status:
        groupers.append(Run.status.label("status"))

    query = (
        db.query(
            date_clause,
            F.count(Run.run_id).label("count"),
            *groupers,
        )
        .filter(
            # TODO: Should get runs for all policy versions.
            (Run.policy_version_id == active_version.active_policy_version_id)
            & (Run.created_at >= start_date)
            & (F.DATE(Run.created_at) <= end_date)
        )
        .group_by(date_clause, *groupers)
    )
    df = pd.read_sql(query.statement, query.session.bind)
    if len(groupers) > 0:
        df = df.pivot(
            index="date", values="count", columns=[c.name for c in groupers]
        ).reset_index()

    return df.to_dict(orient="records")


@router.post("/{policy_id}/runs")
def create_run_by_policy(
    policy_id: int,
    execution_config_str: Annotated[str, Body(embed=True)],
    db: Session = Depends(get_db),
    dagster_client=Depends(get_dagster_client),
    server_config: definitions.VulkanServerConfig = Depends(
        definitions.get_vulkan_server_config
    ),
):
    try:
        execution_config = json.loads(execution_config_str)
    except Exception as e:
        HTTPException(status_code=400, detail=e)

    policy = db.query(Policy).filter_by(policy_id=policy_id).first()
    if policy is None:
        raise HTTPException(status_code=400, detail=f"Policy {policy_id} not found")
    if policy.active_policy_version_id is None:
        raise HTTPException(
            status_code=400,
            detail=f"Policy {policy_id} has no active version",
        )

    version = (
        db.query(PolicyVersion)
        .filter_by(policy_version_id=policy.active_policy_version_id)
        .first()
    )

    run = launch_run(
        dagster_client=dagster_client,
        server_url=server_config.server_url,
        execution_config=execution_config,
        policy_version_id=version.policy_version_id,
        version_name=definitions.version_name(
            version.policy_id, version.policy_version_id
        ),
        db=db,
    )
    return {"policy_id": policy.policy_id, "run_id": run.run_id}
