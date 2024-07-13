import json

from flask import Flask, request
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from .db import Policy, Run
from .trigger_run import trigger_dagster_job

app = Flask(__name__)
engine = create_engine("sqlite:///server/example.db", echo=True)
Session = sessionmaker(bind=engine)


@app.route("/policy/create", methods=["POST"])
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
            repository=repository,
            job_name=job_name,
        )
        session.add(policy)
        session.commit()
        return {"policy_id": policy.policy_id}


@app.route("/policy/<policy_id>")
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


@app.route("/policy/<policy_id>/run", methods=["POST"])
def run_policy(policy_id):
    execution_config_str = request.form["execution_config"]
    print("\n\n\n" + execution_config_str + "\n\n\n")
    execution_config = json.loads(execution_config_str)
    with Session() as session:
        run = Run(policy_id=policy_id, status="pending")
        session.add(run)
        session.commit()

        policy = session.query(Policy).filter_by(policy_id=policy_id).first()
        # Trigger the Dagster job
        dagster_run_id = trigger_dagster_job(
            policy.repository,
            policy.job_name,
            execution_config,
        )
        run.status = "running"
        run.dagster_run_id = dagster_run_id
        session.commit()
        return {"run_id": run.run_id}


# Podemos ter um run_policy_async e um sync
# O sync vai esperar a run terminar e retornar o status
# O async vai retornar o run_id e o status da run vai ser atualizado
# depois via uma chamada nossa para algum endpoint


@app.route("/policy/<policy_id>/run/<run_id>")
def get_run(policy_id, run_id):
    # How do we get the run status from Dagster API?
    with Session() as session:
        run = session.query(Run).filter_by(run_id=run_id).first()
        return {
            "status": run.status,
            "result": run.result,
            "dagster_run_id": run.dagster_run_id,
        }


@app.route("/policy/<policy_id>/run/<run_id>/update")
def update_run(policy_id, run_id):
    with Session() as session:
        run = session.query(Run).filter_by(run_id=run_id).first()
        return {
            "status": run.status,
            "result": run.result,
            "dagster_run_id": run.dagster_run_id,
        }
