from vulkan.cli.context import Context


def create(
    ctx: Context,
    policy_id: str,
    version_name: str,
    spec: dict | None = None,
    input_schema: dict[str, str] | None = None,
    requirements: list[str] | None = None,
):
    # TODO: improve UX by showing a loading animation
    ctx.logger.info(f"Creating workspace {version_name}. This may take a while...")
    if requirements is None:
        requirements = []

    if spec is None:
        spec = {}

    body = {
        "policy_id": policy_id,
        "alias": version_name,
        "spec": spec,
        "requirements": requirements,
        "input_schema": input_schema,
    }

    response = ctx.session.post(
        f"{ctx.server_url}/policy-versions",
        json=body,
    )
    if response.status_code == 400:
        detail = response.json().get("detail", "")
        error = detail.get("error")
        ctx.logger.debug(f"Error: {error}")
        if error == "InvalidDefinitionError":
            ctx.logger.debug(detail)
            raise ValueError(
                "The PolicyDefinition instance was improperly configured. "
                "It may be missing a node or have missing/invalid attributes. "
                "It could also be that an imported python package wasn't specified "
                "as a dependency in the pyproject.toml file."
            )
        if error == "ConflictingDefinitionsError":
            raise ValueError(
                "More than one PolicyDefinition instances was found in the "
                "specified repository."
            )
        raise ValueError(f"Bad request: {detail}")

    if response.status_code != 200:
        raise ValueError(f"Failed to create policy version: {response.content}")

    policy_version = response.json()
    policy_version_id = policy_version["policy_version_id"]
    ctx.logger.info(
        f"Created workspace {version_name} with policy version {policy_version_id}"
    )
    return policy_version


def update(
    ctx: Context,
    policy_version_id: str,
    version_name: str,
    input_schema: dict,
    spec: dict,
    requirements: list[str],
):
    response = ctx.session.put(
        url=f"{ctx.server_url}/policy-versions/{policy_version_id}",
        json={
            "alias": version_name,
            "spec": spec,
            "requirements": requirements,
            "input_schema": input_schema,
        },
    )

    if response.status_code == 400:
        detail = response.json().get("detail", "")
        error = detail.get("error")
        ctx.logger.debug(f"Error: {error}")
        if error == "InvalidDefinitionError":
            ctx.logger.debug(detail)
            raise ValueError(
                "The PolicyDefinition instance was improperly configured. "
                "It may be missing a node or have missing/invalid attributes. "
                "It could also be that an imported python package wasn't specified "
                "as a dependency in the pyproject.toml file."
            )
        if error == "ConflictingDefinitionsError":
            raise ValueError(
                "More than one PolicyDefinition instances was found in the "
                "specified repository."
            )
        raise ValueError(f"Bad request: {detail}")

    if response.status_code != 200:
        raise ValueError(f"Failed to create policy version: {response.content}")

    policy_version = response.json()
    policy_version_id = policy_version["policy_version_id"]
    ctx.logger.info(f"Updated policy version {policy_version_id}")
    return policy_version


def get(ctx: Context, policy_version_id: str):
    response = ctx.session.get(f"{ctx.server_url}/policy-versions/{policy_version_id}")
    if response.status_code != 200:
        raise ValueError(f"Failed to get policy version: {response.content}")
    return response.json()


def list_variables(ctx: Context, policy_version_id: str) -> dict[str, str | None]:
    response = ctx.session.get(
        f"{ctx.server_url}/policy-versions/{policy_version_id}/variables",
    )
    if response.status_code != 200:
        raise ValueError(f"Failed to list variables: {response.content}")
    return response.json()


def set_variables(
    ctx: Context,
    policy_version_id: str,
    variables: dict[str, str],
):
    ctx.logger.info(f"Setting variables: {variables}")
    response = ctx.session.put(
        f"{ctx.server_url}/policy-versions/{policy_version_id}/variables",
        json=variables,
    )
    if response.status_code != 200:
        raise ValueError("Failed to set variables")

    return response.json()


def delete_policy_version(
    ctx: Context,
    policy_version_id: str,
):
    response = ctx.session.delete(
        f"{ctx.server_url}/policy-versions/{policy_version_id}"
    )
    if response.status_code != 200:
        raise ValueError(f"Failed to delete policy version: {response.content}")
    ctx.logger.info(f"Deleted policy version {policy_version_id}")
