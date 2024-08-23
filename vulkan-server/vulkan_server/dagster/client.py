from vulkan_server.dagster.trigger_run import create_dagster_client


def get_dagster_client():
    # TODO: receive as env
    DAGSTER_URL = "dagster"
    DAGSTER_PORT = 3000
    dagster_client = create_dagster_client(DAGSTER_URL, DAGSTER_PORT)
    return dagster_client
