# Create policy
import json

import requests

PORT = 6000
URL = f"http://localhost:{PORT}"

response = requests.post(
    f"{URL}/policy/create",
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
        "config": {"multiprocess": {"max_concurrent": 2, "retries": {"disabled": {}}}}
    },
    "ops": {"input_node": {"config": {"cpf": "1"}}},
}

response = requests.post(
    f"{URL}/policy/{policy_id}/run",
    data={"execution_config": json.dumps(execution_config)},
)
print(response.json())

# Get the run status
run_id = response.json()["run_id"]
response = requests.get(f"{URL}/policy/{policy_id}/run/{run_id}")
print(response.json())
