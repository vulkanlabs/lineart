# Create policy
import argparse
import json
import time

import requests


def run(args):
    url = f"http://localhost:{args.port}"

    response = requests.post(
        f"{url}/policies/create",
        data={
            "name": "test_policy",
            "description": "test_policy_description",
            "input_schema": "test_input_schema",
            "repository": "vulkan_dagster",
            "job_name": "policy_job",
        },
    )

    assert response.status_code == 200
    print(response.json())

    policy_id = response.json()["policy_id"]

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
        try:
            status = response.json()["status"]
            if status == "completed":
                success = True
                print(response.json())
                break
        except (KeyError, json.decoder.JSONDecodeError):
            continue
        time.sleep(3)

    assert success, f"Run {run_id} for policy {policy_id} did not complete successfully"


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, help="Port to run the server on")
    parser.add_argument("--cpf", type=str, help="CPF to test the policy with")
    args = parser.parse_args()
    run(args)
