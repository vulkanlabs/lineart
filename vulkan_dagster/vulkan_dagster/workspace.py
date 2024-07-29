import os
from shutil import make_archive, unpack_archive

from dagster import Definitions, EnvVar, IOManagerDefinition

from .io_manager import (
    DB_CONFIG_KEY,
    DBConfig,
    metadata_io_manager,
    postgresql_io_manager,
)
from .policy import Policy
from .run import RUN_CONFIG_KEY, VulkanRunConfig
from .step_metadata import PUBLISH_IO_MANAGER_KEY


def make_workspace_definition(policies: list[Policy]) -> Definitions:
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
        "io_manager": IOManagerDefinition(
            resource_fn=postgresql_io_manager,
            required_resource_keys={RUN_CONFIG_KEY, DB_CONFIG_KEY},
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
        resources={},
    )
    return definition


ARCHIVE_FORMAT = "gztar"


def pack_workspace(name: str, repository_path: str):
    basename = f".tmp.{name}"
    filename = make_archive(basename, ARCHIVE_FORMAT, repository_path)
    with open(filename, "rb") as f:
        repository = f.read()
    os.remove(filename)
    return repository


def unpack_workspace(base_dir: str, name: str, repository: bytes):
    workspace_path = os.path.join(base_dir, name)
    filepath = f".tmp.{name}"
    with open(filepath, "wb") as f:
        f.write(repository)
    unpack_archive(filepath, workspace_path, format=ARCHIVE_FORMAT)

    os.remove(filepath)

    return workspace_path


def add_workspace_config(base_dir: str, name: str, path: str):
    with open(os.path.join(base_dir, "workspace.yaml"), "a") as ws:
        ws.write(
            (
                "  - python_module:\n"
                f"      module_name: {path}\n"
                f"      working_directory: workspaces/{name}\n"
                f"      executable_path: /opt/venvs/{name}/bin/python\n"
            )
        )
