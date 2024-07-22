from os import getenv

from dagster import Definitions, IOManagerDefinition, load_assets_from_modules

from . import assets
from .io_manager import MyIOManager, metadata_io_manager
from .run import RUN_CONFIG_KEY, VulkanRunConfig
from .step_metadata import PUBLISH_IO_MANAGER_KEY

storage_root_path = getenv("VULKAN_ASSETS_ROOT_PATH")
if storage_root_path is None:
    raise ValueError("VULKAN_ASSETS_ROOT_PATH must be set")

metadata_publish_endpoint = getenv("VULKAN_METADATA_PUBLISH_ENDPOINT")

all_assets = load_assets_from_modules([assets])


run_config = VulkanRunConfig(
    policy_id=0,
    run_id=0,
    server_url="tmpurl",
)

resources = {
    RUN_CONFIG_KEY: run_config,
    PUBLISH_IO_MANAGER_KEY: IOManagerDefinition(
        resource_fn=metadata_io_manager,
        required_resource_keys={RUN_CONFIG_KEY},
    ),
}
jobs = [p.to_job(resources) for p in assets.policies]

defs = Definitions(
    assets=all_assets,
    jobs=jobs,
    resources={
        "io_manager": MyIOManager(root_path=storage_root_path),
    },
)
