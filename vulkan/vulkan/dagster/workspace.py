import os
from shutil import rmtree

import yaml
from dagster import Definitions, EnvVar, IOManagerDefinition

from vulkan.dagster.io_manager import (
    DB_CONFIG_KEY,
    PUBLISH_IO_MANAGER_KEY,
    DBConfig,
    metadata_io_manager,
    postgresql_io_manager,
)
from vulkan.dagster.policy import DagsterFlow
from vulkan.dagster.run_config import RUN_CONFIG_KEY, VulkanRunConfig
from vulkan.environment.loaders import resolve_policy
from vulkan.environment.workspace import VulkanCodeLocation


def make_workspace_definition(
    file_location: str,
    components_base_dir: str,
) -> Definitions:
    resources = {
        # Vulkan Configurable Resources
        RUN_CONFIG_KEY: VulkanRunConfig.configure_at_launch(),
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
    }

    # Up to this point, everything should be defined in terms of core elements.
    # Nodes and components should be configured, resolved, checked in core.
    resolved_policy = resolve_policy(file_location, components_base_dir)
    # From here, each implementation should handle transforming core to its own
    # needs, ie. Core -> Dagster
    # -> Transform nodes in dagster nodes
    dagster_flow = DagsterFlow(
        nodes=resolved_policy.flattened_nodes,
        dependencies=resolved_policy.flattened_dependencies,
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
        code_location: VulkanCodeLocation,
    ) -> None:
        self.base_dir = base_dir
        self.code_location = code_location

    @property
    def definitions_path(self):
        return self._get_definitions_path()

    def add_workspace_config(self, name: str, venvs_path: str):
        with open(os.path.join(self.base_dir, "workspace.yaml"), "a") as ws:
            init_path = os.path.join(self.definitions_path, "__init__.py")
            ws.write(
                (
                    "- python_file:\n"
                    f"    relative_path: {init_path}\n"
                    f"    working_directory: {self.definitions_path}\n"
                    f"    executable_path: {venvs_path}/{name}/bin/python\n"
                    f"    location_name: {name}\n"
                )
            )

    def remove_workspace_config(self, name: str):
        path = os.path.join(self.base_dir, "workspace.yaml")

        with open(path, "r") as fn:
            workspace_config = yaml.safe_load(fn)

        load_from = []
        for location in workspace_config["load_from"]:
            if location.get("python_file", {}).get("location_name") != name:
                load_from.append(location)

        with open(path, "w") as fn:
            yaml.dump(dict(load_from=load_from), fn)

    def create_init_file(self, components_path: str) -> str:
        definitions_path = self.definitions_path
        os.makedirs(definitions_path, exist_ok=True)
        init_path = os.path.join(definitions_path, "__init__.py")

        init_contents = DAGSTER_ENTRYPOINT.format(
            code_entrypoint=self.code_location.entrypoint,
            components_path=components_path,
        )
        with open(init_path, "w") as fp:
            fp.write(init_contents)

        return init_path

    def delete_resources(self, name: str):
        rmtree(self.definitions_path)
        self.remove_workspace_config(name)

    def _get_definitions_path(self):
        # TODO: we're replacing /workspaces with /definitions as a convenience.
        # We could have a more thorough definition of where the defs are stored.
        return self.code_location.working_dir.replace("/workspaces", "/definitions", 1)


DAGSTER_ENTRYPOINT = """
from vulkan.dagster.workspace import make_workspace_definition
                
definitions = make_workspace_definition("{code_entrypoint}", "{components_path}")
"""
