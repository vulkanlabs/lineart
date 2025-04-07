import os

import yaml
from dagster import Definitions, EnvVar, IOManagerDefinition
from vulkan_public.constants import POLICY_CONFIG_KEY

from vulkan.dagster.io_manager import (
    DB_CONFIG_KEY,
    PUBLISH_IO_MANAGER_KEY,
    DBConfig,
    metadata_io_manager,
    postgresql_io_manager,
)
from vulkan.dagster.policy import DagsterFlow
from vulkan.dagster.resources import DATA_CLIENT_KEY, VulkanDataClient
from vulkan.dagster.run_config import (
    RUN_CONFIG_KEY,
    VulkanPolicyConfig,
    VulkanRunConfig,
)
from vulkan.environment.loaders import load_and_resolve_policy


def make_workspace_definition(spec_location: str) -> Definitions:
    run_config = VulkanRunConfig.configure_at_launch()
    resources = {
        # Vulkan Configurable Resources
        RUN_CONFIG_KEY: run_config,
        POLICY_CONFIG_KEY: VulkanPolicyConfig.configure_at_launch(),
        # Run DB
        DB_CONFIG_KEY: DBConfig(
            host=EnvVar("VULKAN_DB_HOST"),
            port=EnvVar("VULKAN_DB_PORT"),
            user=EnvVar("VULKAN_DB_USER"),
            password=EnvVar("VULKAN_DB_PASSWORD"),
            database=EnvVar("VULKAN_DB_DATABASE"),
            object_table=EnvVar("VULKAN_DB_OBJECT_TABLE"),
        ),
        # IO Managers
        "io_manager": IOManagerDefinition(
            resource_fn=postgresql_io_manager,
            required_resource_keys={RUN_CONFIG_KEY, DB_CONFIG_KEY},
        ),
        PUBLISH_IO_MANAGER_KEY: IOManagerDefinition(
            resource_fn=metadata_io_manager,
            required_resource_keys={RUN_CONFIG_KEY},
        ),
        DATA_CLIENT_KEY: VulkanDataClient(run_config=run_config),
    }

    # Up to this point, everything should be defined in terms of core elements.
    # Nodes and components should be configured, resolved, checked in core.
    resolved_policy = load_and_resolve_policy()
    # From here, each implementation should handle transforming core to its own
    # needs, ie. Core -> Dagster
    # -> Transform nodes in dagster nodes
    dagster_flow = DagsterFlow(
        nodes=resolved_policy.nodes,
        dependencies=resolved_policy.edges,
    )
    # By definition, Vulkan dagster worskpaces have a single job.
    jobs = [dagster_flow.to_job(resources)]
    definition = Definitions(
        assets=[],
        jobs=jobs,
        resources={},
    )
    return definition


class DagsterWorkspaceManager:
    def __init__(
        self,
        base_dir: str,
        workspace_path: str,
    ) -> None:
        self.base_dir = base_dir
        self.workspace_path = workspace_path

    def add_workspace_config(self, workspace_id: str):
        with open(os.path.join(self.base_dir, "workspace.yaml"), "a") as ws:
            ws.write(
                (
                    "- python_file:\n"
                    f"    relative_path: {self.workspace_path}/__init__.py\n"
                    f"    working_directory: {self.workspace_path}\n"
                    f"    executable_path: {self.workspace_path}/bin/python\n"
                    f"    location_name: {workspace_id}\n"
                )
            )

    def remove_workspace_config(self, workspace_id: str):
        path = os.path.join(self.base_dir, "workspace.yaml")

        with open(path, "r") as fn:
            workspace_config = yaml.safe_load(fn)

        load_from = []
        for location in workspace_config["load_from"]:
            if location.get("python_file", {}).get("location_name") != workspace_id:
                load_from.append(location)

        with open(path, "w") as fn:
            yaml.dump(dict(load_from=load_from), fn)

    def create_init_file(self) -> str:
        init_path = os.path.join(self.workspace_path, "__init__.py")

        with open(init_path, "w") as fp:
            fp.write(DAGSTER_ENTRYPOINT)

        return init_path

    def delete_resources(self, workspace_id: str):
        self.remove_workspace_config(workspace_id)


DAGSTER_ENTRYPOINT = """
from vulkan.dagster.workspace import make_workspace_definition
                
definitions = make_workspace_definition()
"""
