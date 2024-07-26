from dagster import Definitions, IOManagerDefinition

from .io_manager import MyIOManager, metadata_io_manager
from .run import RUN_CONFIG_KEY, VulkanRunConfig
from .step_metadata import PUBLISH_IO_MANAGER_KEY


def make_workspace_definition(policies):
    resources = {
        RUN_CONFIG_KEY: VulkanRunConfig(
            policy_id=0,
            run_id=0,
            server_url="tmpurl",
        ),
        PUBLISH_IO_MANAGER_KEY: IOManagerDefinition(
            resource_fn=metadata_io_manager,
            required_resource_keys={RUN_CONFIG_KEY},
        ),
    }

    jobs = [p.to_job(resources) for p in policies]

    definition = Definitions(
        assets=[],
        jobs=jobs,
        resources={
            "io_manager": MyIOManager(root_path="/opt/dagster/custom_storage/"),
        },
    )
    return definition
