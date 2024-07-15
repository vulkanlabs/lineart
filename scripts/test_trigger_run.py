# Create policy
import json
import time

import requests

PORT = 6000
URL = f"http://localhost:{PORT}"

response = requests.post(
    f"{URL}/policies/create",
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
        "config": {"multiprocess": {"max_concurrent": 5, "retries": {"disabled": {}}}}
    },
    "ops": {"input_node": {"config": {"cpf": "1"}}},
}

response = requests.post(
    f"{URL}/policies/{policy_id}/runs/create",
    data={"execution_config": json.dumps(execution_config)},
)
print(response.json())

# Get the run status
run_id = response.json()["run_id"]
response = requests.get(f"{URL}/policies/{policy_id}/runs/{run_id}")
print(response.json())

success = False
# Poll the API until the job is completed
for i in range(10):
    response = requests.get(f"{URL}/policies/{policy_id}/runs/{run_id}")
    try:
        status = response.json()["status"]
        if status == "completed":
            success = True
            break
    except (KeyError, json.decoder.JSONDecodeError):
        continue
    time.sleep(1)

assert success, f"Run {run_id} for policy {policy_id} did not complete successfully"
