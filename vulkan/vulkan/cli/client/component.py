from vulkan.cli.context import Context


def create(
    ctx: Context,
    name: str,
    spec: dict | None = None,
    requirements: list[str] | None = None,
):
    ctx.logger.info(f"Creating component {name}. This may take a while...")

    response = ctx.session.post(
        f"{ctx.server_url}/components/",
        json={
            "name": name,
        },
    )

    component_id = response.json()["component_id"]
    ctx.logger.debug(f"Created component {name} with ID {component_id}")
    try:
        return _update_policy_version(
            ctx,
            component_id,
            name,
            spec,
            requirements,
        )
    except Exception as e:
        delete(ctx, component_id)
        raise e


def update(
    ctx: Context,
    component_id: str,
    name: str,
    spec: dict,
    requirements: list[str],
):
    return _update_policy_version(
        ctx,
        component_id,
        name,
        spec,
        requirements,
    )


def get(ctx: Context, component_id: str):
    response = ctx.session.get(f"{ctx.server_url}/components/{component_id}")
    if response.status_code != 200:
        raise ValueError(f"Failed to get component: {response.content}")
    return response.json()


def delete(
    ctx: Context,
    component_id: str,
):
    response = ctx.session.delete(f"{ctx.server_url}/components/{component_id}")
    if response.status_code != 200:
        raise ValueError(f"Failed to delete component: {response.content}")
    ctx.logger.info(f"Deleted component {component_id}")


def _update_policy_version(
    ctx: Context,
    component_id: str,
    name: str,
    spec: dict,
    requirements: list[str],
):
    response = ctx.session.put(
        url=f"{ctx.server_url}/components/{component_id}",
        json={
            "name": name,
            "spec": spec,
            "requirements": requirements,
        },
    )

    if response.status_code == 400:
        detail = response.json().get("detail", "")
        raise ValueError(f"Bad request: {detail}")

    if response.status_code != 200:
        raise ValueError(f"Failed to create component: {response.content}")

    component = response.json()
    component_id = component["component_id"]
    ctx.logger.debug(f"Updated component {name} with ID {component_id}")
    return component
