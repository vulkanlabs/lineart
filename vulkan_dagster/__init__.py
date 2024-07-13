from dagster import Definitions, load_assets_from_modules

from . import assets

all_assets = load_assets_from_modules([assets])

jobs = [p.to_job() for p in assets.policies]

defs = Definitions(
    assets=all_assets,
    jobs=jobs,
)
