import json
import os

import werkzeug.exceptions
from dotenv import load_dotenv
from flask import Flask, request
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from .db import Policy, Run, StepMetadata
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
        return [
            {
                "policy_id": policy.policy_id,
                "name": policy.name,
                "description": policy.description,
                "input_schema": policy.input_schema,
                "repository": policy.repository,
                "job_name": policy.job_name,
            }
            for policy in policies
        ]


@app.route("/policies/create", methods=["POST"])
def create_policy():
    name = request.form["name"]
    description = request.form["description"]
    input_schema = request.form["input_schema"]
    repository = request.form["repository"]
    job_name = request.form["job_name"]

    with Session() as session:
        policy = Policy(
            name=name,
            description=description,
            input_schema=input_schema,
            # git_repo=...,
            # path=...,
            # We should automatically generate this
            repository=repository,
            job_name=job_name,
        )
        session.add(policy)
        session.commit()
        return {"policy_id": policy.policy_id}


@app.route("/policies/<policy_id>")
def get_policy(policy_id):
    with Session() as session:
        policy = session.query(Policy).filter_by(policy_id=policy_id).first()
        return {
            "name": policy.name,
            "description": policy.description,
            "input_schema": policy.input_schema,
            "repository": policy.repository,
            "job_name": policy.job_name,
        }


@app.route("/policies/<policy_id>/runs/create", methods=["POST"])
def create_run(policy_id: int):
    execution_config_str = request.form["execution_config"]
    try:
        execution_config = json.loads(execution_config_str)
    except Exception as e:
        handle_bad_request(e)

    with Session() as session:
        run = Run(policy_id=policy_id, status="PENDING")
        session.add(run)
        session.commit()

        try:
            policy = session.query(Policy).filter_by(policy_id=policy_id).first()
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
            dagster_run_id = trigger_dagster_job(
                policy.repository,
                policy.job_name,
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
            werkzeug.exceptions.InternalServerError(e)


# Podemos ter um run_policy_async e um sync
# O sync vai esperar a run terminar e retornar o status
# O async vai retornar o run_id e o status da run vai ser atualizado
# depois via uma chamada nossa para algum endpoint


@app.route("/policies/<policy_id>/runs/<run_id>", methods=["GET"])
def get_run(policy_id, run_id):
    # How do we get the run status from Dagster API?
    with Session() as session:
        run = session.query(Run).filter_by(policy_id=policy_id, run_id=run_id).first()
        return {
            "policy_id": run.policy_id,
            "run_id": run.run_id,
            "status": run.status,
            "result": run.result,
            "dagster_run_id": run.dagster_run_id,
        }


@app.route("/policies/<policy_id>/runs/<run_id>", methods=["PUT"])
def update_run(policy_id, run_id):
    try:
        result = request.form["result"]
        dagster_run_id = request.form["dagster_run_id"]
        status = request.form["status"]

        with Session() as session:
            run = (
                session.query(Run)
                .filter_by(
                    policy_id=policy_id, run_id=run_id, dagster_run_id=dagster_run_id
                )
                .first()
            )
            run.status = status
            run.result = result
            session.commit()
            return {
                "policy_id": run.policy_id,
                "run_id": run.run_id,
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
