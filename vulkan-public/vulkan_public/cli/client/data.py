import os

import yaml

from vulkan_public.cli.context import Context
from vulkan_public.schemas import DataSourceSpec


def list_data_sources(ctx: Context, include_archived: bool = False) -> list[dict]:
    response = ctx.session.get(
        f"{ctx.server_url}/data-sources",
        params={"include_archived": include_archived},
    )
    assert (
        response.status_code == 200
    ), f"Failed to list data sources: {response.content}"
    return response.json()


def create_data_source(ctx: Context, config: dict) -> str:
    data_source = DataSourceSpec.model_validate(config)

    response = ctx.session.post(
        f"{ctx.server_url}/data-sources",
        json=data_source.model_dump(),
    )
    assert (
        response.status_code == 200
    ), f"Failed to create data source: {response.content}"

    data_source_id = response.json()["data_source_id"]
    ctx.logger.info(f"Created data source {data_source_id}")
    return data_source_id


def get_data_source(ctx: Context, data_source_id: str) -> dict:
    response = ctx.session.get(f"{ctx.server_url}/data-sources/{data_source_id}")
    assert response.status_code == 200, f"Failed to get data source: {response.content}"
    return response.json()


def delete_data_source(ctx: Context, data_source_id: str) -> None:
    response = ctx.session.delete(f"{ctx.server_url}/data-sources/{data_source_id}")
    assert (
        response.status_code == 200
    ), f"Failed to delete data source: {response.content}"
    ctx.logger.info(f"Deleted data source {data_source_id}")


def list_data_objects(ctx: Context, data_source_id: str) -> list[dict]:
    response = ctx.session.get(
        f"{ctx.server_url}/data-sources/{data_source_id}/objects"
    )
    assert response.status_code == 200, f"Failed to get data object: {response.content}"
    return response.json()
