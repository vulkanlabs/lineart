from dagster_graphql import DagsterGraphQLClient

client = DagsterGraphQLClient("localhost", port_number=3000)


# Replace with your Dagster instance URL
# Define a function to trigger a Dagster job
def trigger_dagster_job(job_name, run_config):
    try:
        response = client.submit_job_execution(
            repository_name="vulkan_dagster",
            job_name=job_name,
            run_config=run_config,
        )
        # Process the response if needed
        print(response)
        return response
    except Exception as e:
        # Handle exceptions
        print(f"Error triggering job: {e}")
        return None


# Call the function to trigger the Dagster job
result = trigger_dagster_job(
    "policy_job",
    {
        "execution": {
            "config": {
                "multiprocess": {"max_concurrent": 2, "retries": {"disabled": {}}}
            }
        },
        "ops": {"input_node": {"config": {"cpf": "1"}}},
    },
)
