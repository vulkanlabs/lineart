from dagster_graphql import DagsterGraphQLClient, ReloadRepositoryLocationStatus


def create_dagster_client(url: str, port: int) -> DagsterGraphQLClient:
    return DagsterGraphQLClient(url, port_number=port)


def trigger_dagster_job(
    client: DagsterGraphQLClient,
    repository_name: str,
    job_name: str,
    run_config: dict,
):
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


def update_repository(client: DagsterGraphQLClient) -> dict[str, bool]:
    response = client._execute(RELOAD_WORKSPACE_MUTATION)
    if "reloadWorkspace" not in response.keys():
        raise ValueError(f"Failed to reload workspace: {response}")
    entries = response["reloadWorkspace"]["locationEntries"]
    return {
        # Checks if the repository location was loaded
        # and then if the location load had any errors
        e["name"]: e["loadStatus"] == "LOADED"
        and e["locationOrLoadError"]["__typename"] == "RepositoryLocation"
        for e in entries
    }


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
