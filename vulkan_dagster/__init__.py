from os import getenv

from dagster import Definitions, load_assets_from_modules

from . import assets
from .io_manager import MyIOManager

storage_root_path = getenv("VULKAN_ASSETS_ROOT_PATH")
if storage_root_path is None:
    raise ValueError("VULKAN_ASSETS_ROOT_PATH must be set")

all_assets = load_assets_from_modules([assets])

jobs = [p.to_job() for p in assets.policies]

defs = Definitions(
    assets=all_assets,
    jobs=jobs,
    resources={"io_manager": MyIOManager(root_path=storage_root_path)},
)
