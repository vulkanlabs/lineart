from dagster_graphql import DagsterGraphQLClient

client = DagsterGraphQLClient("dagster", port_number=3000)


# Replace with your Dagster instance URL
# Define a function to trigger a Dagster job
def trigger_dagster_job(repository_name, job_name, run_config):
    try:
        response = client.submit_job_execution(
            repository_name=repository_name,
            job_name=job_name,
            run_config=run_config,
        )
        # Process the response if needed
        return response
    except Exception as e:
        # Handle exceptions
        print(f"Error triggering job: {e}")
        return None
