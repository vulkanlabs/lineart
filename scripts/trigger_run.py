from dagster import DagsterGraphQLClient

# Set up the GraphQL client to communicate with your Dagster instance
dagster_client = DagsterGraphQLClient("<http://localhost:3000/graphql>")


# Replace with your Dagster instance URL
# Define a function to trigger a Dagster job
def trigger_dagster_job(pipeline_name, environment_dict):
    try:
        response = dagster_client.execute_plan(
            pipeline_name=pipeline_name,
            environment_dict=environment_dict,
        )
        # Process the response if needed
        print(response)
        return response
    except Exception as e:
        # Handle exceptions
        print(f"Error triggering job: {e}")
        return None


# Call the function to trigger the Dagster job
result = trigger_dagster_job("your_pipeline_name", {"config_key": "config_value"})
