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
            "requirements": requirements,
        },
    )

    if response.status_code != 200:
        raise ValueError(f"Failed to create component: {response.content}")

    component = response.json()
    component_id = component["component_id"]
    ctx.logger.info(f"Created component {name} with ID {component_id}")

    return _update_component(
        ctx,
        name,
        spec=spec,
        requirements=requirements,
    )


def update(
    ctx: Context,
    name: str,
    spec: dict,
    requirements: list[str],
):
    return _update_component(
        ctx,
        name,
        spec,
        requirements,
    )


def get(ctx: Context, name: str):
    response = ctx.session.get(f"{ctx.server_url}/components/{name}")
    if response.status_code == 404:
        raise ValueError(f"Component {name} not found")
    if response.status_code != 200:
        raise ValueError(f"Failed to get component: {response.content}")
    return response.json()


def delete(
    ctx: Context,
    name: str,
):
    response = ctx.session.delete(f"{ctx.server_url}/components/{name}")
    if response.status_code != 200:
        raise ValueError(f"Failed to delete component: {response.content}")
    ctx.logger.info(f"Deleted component {name}")


def _update_component(
    ctx: Context,
    name: str,
    spec: dict,
    requirements: list[str],
):
    response = ctx.session.put(
        url=f"{ctx.server_url}/components/{name}",
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
        raise ValueError(f"Failed to update component: {response.content}")

    component = response.json()
    component_id = component["component_id"]
    ctx.logger.debug(f"Updated component {name} with ID {component_id}")
    return component


def _update_component(
    ctx: Context,
    name: str,
    spec: dict,
    requirements: list[str],
):
    response = ctx.session.put(
        url=f"{ctx.server_url}/components/{name}",
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
        raise ValueError(f"Failed to update component: {response.content}")

    component = response.json()
    component_id = component["component_id"]
    ctx.logger.debug(f"Updated component {name} with ID {component_id}")
    return component


def create_or_update(
    ctx: Context,
    name: str,
    spec: dict,
    requirements: list[str],
):
    ctx.logger.info(f"Creating or updating component {name}. This may take a while...")
    try:
        get(ctx, name)
        return update(ctx, name, spec, requirements)
    except ValueError:
        return create(ctx, name, spec, requirements)
