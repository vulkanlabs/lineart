from typing import Annotated
import json
import logging
import os

import requests
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Response, Body, Form, File
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from .db import Policy, PolicyVersion, Run, StepMetadata
from .trigger_run import (
    create_dagster_client,
    trigger_dagster_job,
    update_repository,
)
from . import schemas

app = FastAPI()

logger = logging.getLogger("uvicorn.error")
logger.setLevel(logging.INFO)

engine = create_engine("sqlite:///server/example.db", echo=True)
Session = sessionmaker(bind=engine)

load_dotenv()
SERVER_URL = f"http://app:{os.getenv('APP_PORT')}"
VULKAN_DAGSTER_SERVER_URL = os.getenv("VULKAN_DAGSTER_SERVER_URL")

DAGSTER_URL = "dagster"
DAGSTER_PORT = 3000
dagster_client = create_dagster_client(DAGSTER_URL, DAGSTER_PORT)
logger.info(f"Dagster client created at http://{DAGSTER_URL}:{DAGSTER_PORT}")


@app.get("/policies/list", response_model=list[schemas.Policy])
def list_policies():
    with Session() as session:
        policies = session.query(Policy).all()
        if len(policies) == 0:
            return Response(status=204)
        return policies


@app.get("/policies/{policy_id}", response_model=schemas.Policy)
def get_policy(policy_id):
    with Session() as session:
        policy = session.query(Policy).filter_by(policy_id=policy_id).first()
        if policy is None:
            return Response(status=204)
        return policy


@app.post("/policies/create")
def create_policy(config: schemas.PolicyBase):
    with Session() as session:
        policy = Policy(**config.model_dump())
        session.add(policy)
        session.commit()
        logger.info(f"Policy {config.name} created")
        return {"policy_id": policy.policy_id, "name": policy.name}


@app.put("/policies/{policy_id}/update")
def update_policy(
    policy_id: int, active_policy_version_id: Annotated[int, Body(embed=True)]
):
    with Session() as session:
        policy = session.query(Policy).filter_by(policy_id=policy_id).first()
        if policy is None:
            msg = f"Tried to update non-existent policy {policy_id}"
            return HTTPException(status_code=400, detail=msg)

        policy_version = (
            session.query(PolicyVersion)
            .filter_by(policy_version_id=active_policy_version_id)
            .first()
        )
        if policy_version is None:
            msg = f"Tried to use non-existent version {active_policy_version_id} for policy {policy_id}"
            return HTTPException(status_code=400, detail=msg)

        policy.active_policy_version_id = active_policy_version_id
        session.commit()
        msg = f"Policy {policy_id} updated: active version set to {active_policy_version_id}"
        logger.info(msg)
        return {
            "policy_id": policy.policy_id,
            "active_policy_version_id": policy.active_policy_version_id,
        }


@app.get(
    "/policies/{policy_id}/versions/list",
    response_model=list[schemas.PolicyVersion],
)
def list_policy_versions(policy_id: int):
    with Session() as session:
        policy_versions = (
            session.query(PolicyVersion).filter_by(policy_id=policy_id).all()
        )
        if len(policy_versions) == 0:
            return Response(status=204)
        return policy_versions


# TODO: evaluate whether policy_id should be a path parameter or a form parameter
@app.post("/policies/{policy_id}/versions/create")
def create_policy_version(
    policy_id: int,
    config: schemas.PolicyVersionBase,
):
    logger.info(f"Creating policy version for policy {policy_id}")
    if config.alias is None:
        # We can use the repo version as an easy alias or generate one.
        # This should ideally be a commit hash or similar, indicating a
        # unique version of the code.
        config.alias = config.repository_version

    with Session() as session:
        policy = session.query(Policy).filter_by(policy_id=policy_id).first()
        if policy is None:
            msg = (
                f"Tried to create a version for non-existent policy {policy_id}"
            )
            return HTTPException(status_code=400, detail=msg)

        # Create workspace
        try:
            status_code = _create_policy_version_workspace(
                VULKAN_DAGSTER_SERVER_URL,
                config.alias,
                config.entrypoint,
                config.repository,
            )
            if status_code != 200:
                raise ValueError(f"Failed to create workspace: {status_code}")
        except Exception as e:
            msg = f"Failed to create workspace for policy {policy_id} version {config.alias}"
            logger.error(msg)
            return HTTPException(status_code=500, detail=e)

        args = {**config.model_dump(), "repository": config.repository}
        version = PolicyVersion(**args)
        session.add(version)
        session.commit()
        logger.info(
            f"Policy version {config.alias} created for policy {policy_id}"
        )

        try:
            update_repository(dagster_client)
            logger.info(f"Updated repository {config.alias} successfully")
        except ValueError as e:
            logger.warn(f"Failed to update repositories: {e}")

        return {
            "policy_id": policy_id,
            "policy_version_id": version.policy_version_id,
            "alias": version.alias,
        }


def _create_policy_version_workspace(
    vulkan_dagster_server_url: str,
    name: str,
    workspace: str,
    repository: str,
) -> int:
    server_url = f"{vulkan_dagster_server_url}/workspaces/create"
    response = requests.post(
        server_url,
        data={"name": name, "path": workspace, "repository": repository},
    )

    return response.status_code


@app.post("/policies/{policy_id}/runs/create")
def create_run(
    policy_id: int, execution_config_str: Annotated[str, Body(embed=True)]
):
    try:
        execution_config = json.loads(execution_config_str)
    except Exception as e:
        HTTPException(status_code=400, detail=e)

    with Session() as session:
        policy = session.query(Policy).filter_by(policy_id=policy_id).first()
        if policy is None:
            return HTTPException(
                status_code=400, detail=f"Policy {policy_id} not found"
            )
        if policy.active_policy_version_id is None:
            return HTTPException(
                status_code=400,
                detail=f"Policy {policy_id} has no active version",
            )

        version = (
            session.query(PolicyVersion)
            .filter_by(
                policy_id=policy_id,
                policy_version_id=policy.active_policy_version_id,
            )
            .first()
        )

        run = Run(policy_version_id=version.policy_version_id, status="PENDING")
        session.add(run)
        session.commit()

        try:
            # Trigger the Dagster job with Policy and Run IDs as inputs
            execution_config["resources"] = {
                "vulkan_run_config": {
                    "config": {
                        "policy_id": policy.policy_id,
                        "run_id": run.run_id,
                        "server_url": SERVER_URL,
                    }
                }
            }
            # TODO: this could be specified separately as the definition of
            # a dagster-workspace backing the policy version. This is a
            # workaround for now.
            dagster_run_id = trigger_dagster_job(
                dagster_client,
                version.entrypoint,
                "policy",
                execution_config,
            )
            if dagster_run_id is None:
                raise Exception("Error triggering job")

            run.status = "STARTED"
            run.dagster_run_id = dagster_run_id
            session.commit()
            return {"policy_id": policy.policy_id, "run_id": run.run_id}

        except Exception as e:
            run.status = "failed"
            session.commit()
            return HTTPException(status_code=500, detail=e)


# Podemos ter um run_policy_async e um sync
# O sync vai esperar a run terminar e retornar o status
# O async vai retornar o run_id e o status da run vai ser atualizado
# depois via uma chamada nossa para algum endpoint


@app.get("/policies/{policy_id}/runs/{run_id}", response_model=schemas.Run)
def get_run(policy_id: int, run_id: int):
    with Session() as session:
        run = session.query(Run).filter_by(run_id=run_id).first()
        if run is None:
            return HTTPException(
                status_code=400, detail=f"Run {run_id} not found"
            )
        return run


@app.put("/policies/{policy_id}/runs/{run_id}", response_model=schemas.Run)
def update_run(
    policy_id: int,
    run_id: int,
    status: Annotated[str, Body()],
    result: Annotated[str, Body()],
):
    try:
        with Session() as session:
            run = session.query(Run).filter_by(run_id=run_id).first()
            if run is None:
                return HTTPException(
                    status_code=400, detail=f"Run {run_id} not found"
                )

            run.status = status
            run.result = result
            session.commit()
            return run
    except KeyError as e:
        HTTPException(status_code=400, detail=e)


# Add Policy metrics endpoint
# It should calculate the number of executions, average execution time,
# Distribution of run outcomes (approved, analysis, denied) and the success rate
# over time, per day.
# The user should be able to filter by policy_id, date range, and run outcome.
@app.get("/policies/{policy_id}/metrics")
def get_policy_metrics(policy_id: int):
    pass


# TODO: evaluate whether run_id should be a path parameter or a form parameter
@app.post("/policies/{policy_id}/runs/{run_id}/metadata")
def publish_metadata(
    policy_id: int, run_id: int, config: schemas.StepMetadataBase
):
    try:
        with Session() as session:
            args = {"run_id": run_id, **config.model_dump()}
            meta = StepMetadata(**args)
            session.add(meta)
            session.commit()
            return {"status": "success"}
    except KeyError as e:
        return HTTPException(status_code=400, detail=e)
    except Exception as e:
        return HTTPException(status_code=500, detail=e)


@app.post("/components/create")
def create_component(
    name: Annotated[str, Form()], repository: Annotated[bytes, Form()]
):
    try:
        server_url = f"{VULKAN_DAGSTER_SERVER_URL}/components/create"
        response = requests.post(
            server_url,
            data={"name": name, "repository": repository},
        )
        if response.status_code != 200:
            raise ValueError(
                f"Failed to create component: {response.status_code}"
            )
    except Exception as e:
        msg = f"Failed to create component {name}"
        logger.error(msg)
        return HTTPException(status_code=500, detail=e)

    return {"status": "success"}
