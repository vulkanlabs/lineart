from dagster import Definitions, EnvVar, IOManagerDefinition, load_assets_from_modules

from vulkan_dagster import assets
from vulkan_dagster.io_manager import (
    DB_CONFIG_KEY,
    POSTGRES_IO_MANAGER_KEY,
    DBConfig,
    metadata_io_manager,
    postgresql_io_manager,
)
from vulkan_dagster.run import RUN_CONFIG_KEY, VulkanRunConfig
from vulkan_dagster.step_metadata import PUBLISH_IO_MANAGER_KEY

resources = {
    RUN_CONFIG_KEY: VulkanRunConfig(
        policy_id=0,
        run_id=0,
        server_url="tmpurl",
    ),
    DB_CONFIG_KEY: DBConfig(
        host=EnvVar("VULKAN_DB_HOST"),
        port=EnvVar("VULKAN_DB_PORT"),
        user=EnvVar("VULKAN_DB_USER"),
        password=EnvVar("VULKAN_DB_PASSWORD"),
        database=EnvVar("VULKAN_DB_DATABASE"),
        object_table=EnvVar("VULKAN_DB_OBJECT_TABLE"),
    ),
    POSTGRES_IO_MANAGER_KEY: IOManagerDefinition(
        resource_fn=postgresql_io_manager,
        required_resource_keys={RUN_CONFIG_KEY, DB_CONFIG_KEY},
    ),
    PUBLISH_IO_MANAGER_KEY: IOManagerDefinition(
        resource_fn=metadata_io_manager,
        required_resource_keys={RUN_CONFIG_KEY},
    ),
}
jobs = [p.to_job(resources) for p in assets.policies]

defs = Definitions(
    jobs=jobs,
    resources={
        "io_manager": IOManagerDefinition(
            resource_fn=postgresql_io_manager,
            required_resource_keys={RUN_CONFIG_KEY, DB_CONFIG_KEY},
        ),
    },
)
