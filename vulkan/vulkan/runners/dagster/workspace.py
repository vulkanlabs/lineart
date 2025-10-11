import os

import yaml
from dagster import Definitions, EnvVar, IOManagerDefinition

from vulkan.runners.dagster.io_manager import (
    DB_CONFIG_KEY,
    DBConfig,
    postgresql_io_manager,
)
from vulkan.runners.dagster.policy import DagsterFlow
from vulkan.runners.dagster.resources import (
    AppClientResource,
    VulkanPolicyConfig,
    VulkanRunConfig,
)
from vulkan.runners.shared.constants import (
    APP_CLIENT_KEY,
    POLICY_CONFIG_KEY,
    RUN_CONFIG_KEY,
)
from vulkan.spec.environment.loaders import load_and_resolve_policy


def make_workspace_definition(spec_file_path: str) -> Definitions:
    run_config = VulkanRunConfig.configure_at_launch()
    resources = {
        # Vulkan Configurable Resources
        RUN_CONFIG_KEY: run_config,
        POLICY_CONFIG_KEY: VulkanPolicyConfig.configure_at_launch(),
        # Run DB
        DB_CONFIG_KEY: DBConfig(
            host=EnvVar("VULKAN_DB_HOST"),
            port=EnvVar.int("VULKAN_DB_PORT"),
            user=EnvVar("VULKAN_DB_USER"),
            password=EnvVar("VULKAN_DB_PASSWORD"),
            database=EnvVar("VULKAN_DB_DATABASE"),
            object_table=EnvVar("VULKAN_DB_OBJECT_TABLE"),
        ),
        # Unified App Client
        APP_CLIENT_KEY: AppClientResource(run_config=run_config),
        # IO Managers
        "io_manager": IOManagerDefinition(
            resource_fn=postgresql_io_manager,
            required_resource_keys={RUN_CONFIG_KEY, DB_CONFIG_KEY},
        ),
    }

    # Up to this point, everything should be defined in terms of core elements.
    # Nodes and components should be configured, resolved, checked in core.
    resolved_policy = load_and_resolve_policy(spec_file_path)
    # From here, each implementation should handle transforming core to its own
    # needs, ie. Core -> Dagster
    # -> Transform nodes in dagster nodes
    dagster_flow = DagsterFlow(nodes=resolved_policy.nodes)
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
        workspace_file = os.path.join(self.base_dir, "workspace.yaml")
        with open(workspace_file, "r") as fp:
            workspace_config = yaml.safe_load(fp)

        for cfg in workspace_config["load_from"]:
            if cfg.get("python_file", {}).get("location_name") == workspace_id:
                return

        # If we get here, the workspace_id is not in the config file
        new_config = {
            "python_file": {
                "relative_path": f"{self.workspace_path}/__init__.py",
                "working_directory": self.workspace_path,
                "executable_path": f"{self.workspace_path}/.venv/bin/python",
                "location_name": workspace_id,
            }
        }
        workspace_config["load_from"].append(new_config)
        with open(workspace_file, "w") as fp:
            yaml.dump(workspace_config, fp)

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
            init_contents = DAGSTER_ENTRYPOINT.format(
                spec_file_path=os.path.join(self.workspace_path, "policy.json"),
            )
            fp.write(init_contents)

        return init_path

    def delete_resources(self, workspace_id: str):
        self.remove_workspace_config(workspace_id)


DAGSTER_ENTRYPOINT = """
from vulkan.runners.dagster.workspace import make_workspace_definition

definitions = make_workspace_definition("{spec_file_path}")
"""
