import json
import os

import requests
import werkzeug.exceptions
from dotenv import load_dotenv
from flask import Flask, Response, request
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from .db import Policy, PolicyVersion, Run, StepMetadata
from .trigger_run import trigger_dagster_job

app = Flask(__name__)
engine = create_engine("sqlite:///server/example.db", echo=True)
Session = sessionmaker(bind=engine)

load_dotenv()
SERVER_URL = f"http://app:{os.getenv('APP_PORT')}"


@app.route("/policies/list", methods=["GET"])
def list_policies():
    with Session() as session:
        policies = session.query(Policy).all()
        if len(policies) == 0:
            return Response(status=204)

        return [
            {
                "policy_id": policy.policy_id,
                "name": policy.name,
                "description": policy.description,
                "input_schema": policy.input_schema,
                "output_schema": policy.output_schema,
                "active_policy_version_id": policy.active_policy_version_id,
                "created_at": policy.created_at,
                "last_updated_at": policy.last_updated_at,
            }
            for policy in policies
        ]


@app.route("/policies/<policy_id>")
def get_policy(policy_id):
    with Session() as session:
        policy = session.query(Policy).filter_by(policy_id=policy_id).first()
        if policy is None:
            return Response(status=204)

        return {
            "policy_id": policy.policy_id,
            "name": policy.name,
            "description": policy.description,
            "input_schema": policy.input_schema,
            "output_schema": policy.output_schema,
            "active_policy_version_id": policy.active_policy_version_id,
            "created_at": policy.created_at,
            "last_updated_at": policy.last_updated_at,
        }


@app.route("/policies/create", methods=["POST"])
def create_policy():
    name = request.form["name"]
    description = request.form["description"]
    input_schema = request.form["input_schema"]
    output_schema = request.form["output_schema"]

    with Session() as session:
        policy = Policy(
            name=name,
            description=description,
            input_schema=input_schema,
            output_schema=output_schema,
        )
        session.add(policy)
        session.commit()
        app.logger.info(f"Policy {name} created")
        return {"policy_id": policy.policy_id, "name": policy.name}


@app.route("/policies/<policy_id>/update", methods=["PUT"])
def update_policy(policy_id):
    active_policy_version_id = request.form["active_policy_version_id"]
    with Session() as session:
        policy = session.query(Policy).filter_by(policy_id=policy_id).first()
        if policy is None:
            msg = f"Tried to update non-existent policy {policy_id}"
            return werkzeug.exceptions.BadRequest(msg)

        policy_version = (
            session.query(PolicyVersion)
            .filter_by(policy_version_id=active_policy_version_id)
            .first()
        )
        if policy_version is None:
            msg = f"Tried to use non-existent version {active_policy_version_id} for policy {policy_id}"
            return werkzeug.exceptions.BadRequest(msg)

        policy.active_policy_version_id = active_policy_version_id
        session.commit()
        msg = f"Policy {policy_id} updated: active version set to {active_policy_version_id}"
        app.logger.info(msg)
        return {
            "policy_id": policy.policy_id,
            "active_policy_version_id": policy.active_policy_version_id,
        }


@app.route("/policies/<policy_id>/versions/list", methods=["GET"])
def list_policy_versions(policy_id):
    with Session() as session:
        policy_versions = (
            session.query(PolicyVersion).filter_by(policy_id=policy_id).all()
        )
        if len(policy_versions) == 0:
            return Response(status=204)

        return [
            {
                "policy_id": version.policy_id,
                "policy_version_id": version.policy_version_id,
                "alias": version.alias,
                "repository": version.repository,
                "repository_version": version.repository_version,
                "entrypoint": version.entrypoint,
                "created_at": version.created_at,
                "last_updated_at": version.last_updated_at,
            }
            for version in policy_versions
        ]


# TODO: this should create the underlying dagster workspace for the version.
@app.route("/policies/<policy_id>/versions/create", methods=["POST"])
def create_policy_version(policy_id):
    repository = request.form["repository"]
    repository_version = request.form["repository_version"]
    entrypoint = request.form["entrypoint"]
    alias = request.form.get("alias", None)
    if alias is None:
        # We can use the repo version as an easy alias or generate one.
        # This should ideally be a commit hash or similar, indicating a
        # unique version of the code.
        alias = request.form["repository_version"]

    with Session() as session:
        policy = session.query(Policy).filter_by(policy_id=policy_id).first()
        if policy is None:
            msg = f"Tried to create a version for non-existent policy {policy_id}"
            return werkzeug.exceptions.BadRequest(msg)

        # Create workspace
        # try:
        #     status_code = _create_policy_version_workspace()
        #     if status_code != 200:
        #         raise ValueError(f"Failed to create workspace: {status_code}")
        # except Exception as e:
        #     msg = f"Failed to create workspace for policy {policy_id} version {version.policy_version_id}"
        #     app.logger.error(msg)
        #     return werkzeug.exceptions.InternalServerError(e)

        version = PolicyVersion(
            policy_id=policy.policy_id,
            alias=alias,
            repository=repository,
            repository_version=repository_version,
            entrypoint=entrypoint,
        )
        session.add(version)
        session.commit()
        app.logger.info(f"Policy version {alias} created for policy {policy_id}")
        return {
            "policy_id": policy_id,
            "policy_version_id": version.policy_version_id,
            "alias": version.alias,
        }


def _create_policy_version_workspace(
    name: str,
    workspace: str,
    repository: bytes,
) -> int:
    response = requests.post(
        "http://localhost:3001/workspace/create",
        data={"name": name, "path": workspace, "repository": repository},
    )

    return response.status_code


@app.route("/policies/<policy_id>/runs/create", methods=["POST"])
def create_run(policy_id: int):
    execution_config_str = request.form["execution_config"]
    try:
        execution_config = json.loads(execution_config_str)
    except Exception as e:
        handle_bad_request(e)

    with Session() as session:
        policy = session.query(Policy).filter_by(policy_id=policy_id).first()
        if policy is None:
            return werkzeug.exceptions.BadRequest(f"Policy {policy_id} not found")
        if policy.active_policy_version_id is None:
            return werkzeug.exceptions.BadRequest(
                f"Policy {policy_id} has no active version"
            )

        version = (
            session.query(PolicyVersion)
            .filter_by(
                policy_id=policy_id, policy_version_id=policy.active_policy_version_id
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
                version.entrypoint,
                "policy_job",
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
            return werkzeug.exceptions.InternalServerError(e)


# Podemos ter um run_policy_async e um sync
# O sync vai esperar a run terminar e retornar o status
# O async vai retornar o run_id e o status da run vai ser atualizado
# depois via uma chamada nossa para algum endpoint


@app.route("/policies/<policy_id>/runs/<run_id>", methods=["GET"])
def get_run(policy_id, run_id):
    with Session() as session:
        run = session.query(Run).filter_by(run_id=run_id).first()
        return {
            "run_id": run.run_id,
            "policy_version_id": run.policy_version_id,
            "status": run.status,
            "result": run.result,
            "dagster_run_id": run.dagster_run_id,
        }


@app.route("/policies/<policy_id>/runs/<run_id>", methods=["PUT"])
def update_run(policy_id, run_id):
    try:
        result = request.form["result"]
        status = request.form["status"]

        with Session() as session:
            run = session.query(Run).filter_by(run_id=run_id).first()
            if run is None:
                return werkzeug.exceptions.BadRequest(f"Run {run_id} not found")

            run.status = status
            run.result = result
            session.commit()
            return {
                "run_id": run.run_id,
                "policy_version_id": run.policy_version_id,
                "status": run.status,
                "result": run.result,
                "dagster_run_id": run.dagster_run_id,
            }
    except KeyError as e:
        handle_bad_request(e)


@app.errorhandler(werkzeug.exceptions.BadRequest)
def handle_bad_request(e):
    return "Bad Request", 400


# Add Policy metrics endpoint
# It should calculate the number of executions, average execution time,
# Distribution of run outcomes (approved, analysis, denied) and the success rate
# over time, per day.
# The user should be able to filter by policy_id, date range, and run outcome.
@app.route("/policies/<policy_id>/metrics", methods=["GET"])
def get_policy_metrics(policy_id):
    pass


@app.route("/policies/<policy_id>/runs/<run_id>/metadata", methods=["POST"])
def publish_metadata(policy_id, run_id):
    try:
        step_name = request.form["step_name"]
        node_type = request.form["node_type"]
        start_time = request.form["start_time"]
        end_time = request.form["end_time"]
        error = request.form.get("error", None)

        with Session() as session:
            meta = StepMetadata(
                policy_id=policy_id,
                run_id=run_id,
                step_name=step_name,
                node_type=node_type,
                start_time=start_time,
                end_time=end_time,
                error=error,
            )
            session.add(meta)
            session.commit()
            return {"status": "success"}
    except KeyError as e:
        return werkzeug.exceptions.BadRequest(e)
    except Exception as e:
        return werkzeug.exceptions.InternalServerError(e)
