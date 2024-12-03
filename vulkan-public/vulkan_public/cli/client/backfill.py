from pandas import DataFrame

from vulkan_public.cli.context import Context


def list_backfills(ctx: Context):
    response = ctx.session.get(f"{ctx.server_url}/backfills")
    assert response.status_code == 200, f"Failed to list backfills: {response.content}"
    return response.json()


def get_backfill(ctx: Context, backfill_id: str):
    response = ctx.session.get(f"{ctx.server_url}/backfills/{backfill_id}")
    assert response.status_code == 200, f"Failed to list backfills: {response.content}"
    return response.json()


def get_backfill_status(ctx: Context, backfill_id: str):
    response = ctx.session.get(f"{ctx.server_url}/backfills/{backfill_id}/status")
    assert (
        response.status_code == 200
    ), f"Failed to get backfill state: {response.content}"
    return response.json()


def get_results(ctx: Context, backfill_id: str):
    url = f"{ctx.server_url}/backfills/{backfill_id}/results"
    response = ctx.session.get(url)
    if response.status_code != 200:
        raise Exception(f"Failed to get backfill results: {response.content}")
    return DataFrame(response.json())


def download_results_to_file(ctx: Context, backfill_id: str, filename: str):
    url = f"{ctx.server_url}/backfills/{backfill_id}/results"
    response = ctx.session.get(url, stream=True)

    with open(filename, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)

    ctx.logger.info(f"Downloaded results to {filename}")
