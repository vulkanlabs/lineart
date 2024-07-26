import argparse
import json
import os
import time

import requests
from dotenv import load_dotenv


def create_policy(server_url: str, name: str, repository: str, job_name: str):
    response = requests.post(
        f"{server_url}/policies/create",
        data={
            "name": name,
            "description": "test_policy_description",
            "input_schema": "test_input_schema",
            "repository": repository,
            "job_name": job_name,
        },
    )

    assert response.status_code == 200
    print(response.json())

    policy_id = response.json()["policy_id"]
    return policy_id


def run_policy(url: str, policy_id: int):
    # Call the function to trigger the Dagster job
    execution_config = {
        "execution": {
            "config": {
                "multiprocess": {
                    "max_concurrent": 5,
                    "retries": {"disabled": {}},
                }
            }
        },
        "ops": {"input_node": {"config": {"cpf": args.cpf}}},
    }

    response = requests.post(
        f"{url}/policies/{policy_id}/runs/create",
        data={"execution_config": json.dumps(execution_config)},
    )
    print(response.json())

    # Get the run status
    run_id = response.json()["run_id"]
    response = requests.get(f"{url}/policies/{policy_id}/runs/{run_id}")
    print(response.json())

    success = False
    # Poll the API until the job is completed
    for i in range(5):
        response = requests.get(f"{url}/policies/{policy_id}/runs/{run_id}")
        print(response.json())
        try:
            status = response.json()["status"]
            if status == "SUCCESS":
                success = True
                break
        except (KeyError, json.decoder.JSONDecodeError):
            continue
        time.sleep(3)

    assert (
        success
    ), f"Run {run_id} for policy {policy_id} did not complete successfully"


if __name__ == "__main__":
    load_dotenv()
    parser = argparse.ArgumentParser()

    command = parser.add_subparsers(dest="command")
    create = command.add_parser("create")
    create.add_argument(
        "--name", type=str, help="Name of the policy to be created"
    )
    create.add_argument(
        "--repository", type=str, help="Repository of the policy to be created"
    )
    create.add_argument(
        "--job_name", type=str, help="Job name of the policy to be created"
    )

    run = command.add_parser("run")
    run.add_argument("--cpf", type=str, help="CPF to test the policy with")
    run.add_argument("--policy_id", type=int, help="Policy ID to run")

    args = parser.parse_args()
    server_url = f"http://localhost:{os.getenv('APP_PORT')}"

    if args.command == "create":
        policy_id = create_policy(
            server_url, args.name, args.repository, args.job_name
        )
    elif args.command == "run":
        policy_id = args.policy_id
        run_policy(server_url, policy_id=policy_id)
    else:
        raise ValueError(f"Invalid command {args.command}")
