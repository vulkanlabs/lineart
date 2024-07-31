from dagster_graphql import DagsterGraphQLClient, ReloadRepositoryLocationStatus


def create_dagster_client(url: str, port: int) -> DagsterGraphQLClient:
    return DagsterGraphQLClient(url, port_number=port)


_DEFAULT_REPOSITORY_NAME = "__repository__"


def trigger_dagster_job(
    client: DagsterGraphQLClient,
    repository_location_name: str,
    job_name: str,
    run_config: dict,
):
    try:
        response = client.submit_job_execution(
            repository_location_name=repository_location_name,
            repository_name=_DEFAULT_REPOSITORY_NAME,
            job_name=job_name,
            run_config=run_config,
        )
        # Process the response if needed
        return response
    except Exception as e:
        # Handle exceptions
        print(f"Error triggering job: {e}")
        return None


def update_repository(client: DagsterGraphQLClient) -> dict[str, bool]:
    response = client._execute(RELOAD_WORKSPACE_MUTATION)
    if "reloadWorkspace" not in response.keys():
        raise ValueError(f"Failed to reload workspace: {response}")
    entries = response["reloadWorkspace"]["locationEntries"]
    return {e["name"]: _check_location_status(e) for e in entries}


def _check_location_status(entry: dict) -> bool:
    keys = set(entry.keys())
    return (
        "loadStatus" in keys
        and entry["loadStatus"] == "LOADED"
        and "locationOrLoadError" in keys
        and entry["locationOrLoadError"]["__typename"] == "RepositoryLocation"
    )


RELOAD_WORKSPACE_MUTATION = """
mutation ReloadWorkspaceMutation {
  reloadWorkspace {
    ... on Workspace {
      id
      locationEntries {
        name
        id
        loadStatus
        locationOrLoadError {
          ...PythonErrorFragment
          __typename
        }
        __typename
      }
      __typename
    }
    ...UnauthorizedErrorFragment
    ...PythonErrorFragment
    __typename
  }
}

fragment UnauthorizedErrorFragment on UnauthorizedError {
      message
  __typename
}

fragment PythonErrorFragment on PythonError {
      message
  stack
  errorChain {
        ...PythonErrorChain
    __typename
  }
  __typename
}

fragment PythonErrorChain on ErrorChainLink {
      isExplicitLink
  error {
        message
    stack
    __typename
  }
  __typename
}

"""
