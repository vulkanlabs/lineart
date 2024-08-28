import argparse
import json
import os
import time

import requests
from dotenv import load_dotenv


def run_policy(url: str, policy_id: int, data: dict):
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
        "ops": {"input_node": {"config": data}},
    }

    response = requests.post(
        f"{url}/policies/{policy_id}/runs",
        json={"execution_config_str": json.dumps(execution_config)},
    )
    print(response.json())

    # Get the run status
    run_id = response.json()["run_id"]
    response = requests.get(f"{url}/runs/{run_id}")
    print(response.json())

    success = False
    # Poll the API until the job is completed
    for i in range(5):
        response = requests.get(f"{url}/runs/{run_id}")
        print(response.json())
        try:
            status = response.json()["status"]
            if status == "SUCCESS":
                success = True
                break
        except (KeyError, json.decoder.JSONDecodeError):
            continue
        time.sleep(3)

    assert success, f"Run {run_id} for policy {policy_id} did not complete successfully"


if __name__ == "__main__":
    load_dotenv()
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=str, help="Data as a JSON string")
    parser.add_argument("--policy_id", type=int, help="Policy ID to run")
    args = parser.parse_args()

    server_url = f"http://localhost:{os.getenv('APP_PORT')}"

    policy_id = args.policy_id
    data = json.loads(args.data)
    run_policy(server_url, policy_id=policy_id, data=data)
