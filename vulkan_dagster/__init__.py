from dagster import RunConfig, Definitions, load_assets_from_modules

from . import assets
from . import policy

all_assets = load_assets_from_modules([assets])

defs = Definitions(
    assets=all_assets,
    jobs=[assets.graph.to_job("policy_job")],
)
