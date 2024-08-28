import os
import tarfile
from shutil import unpack_archive

from dagster import Definitions, EnvVar, IOManagerDefinition

from vulkan.dagster.io_manager import (
    DB_CONFIG_KEY,
    PUBLISH_IO_MANAGER_KEY,
    DBConfig,
    metadata_io_manager,
    postgresql_io_manager,
)
from vulkan.dagster.policy import DagsterPolicy
from vulkan.dagster.run_config import RUN_CONFIG_KEY, VulkanRunConfig


def make_workspace_definition(policy: DagsterPolicy) -> Definitions:
    resources = {
        RUN_CONFIG_KEY: VulkanRunConfig(
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

    # By definition, Vulkan dagster worskpaces have a single job.
    jobs = [policy.to_job(resources)]
    definition = Definitions(
        assets=[],
        jobs=jobs,
        resources={},
    )
    return definition


_ARCHIVE_FORMAT = "gztar"
_TAR_FLAGS = "w:gz"
_EXCLUDE_PATHS = [".git", ".venv"]


def pack_workspace(name: str, repository_path: str):
    basename = f".tmp.{name}"
    # TODO: In the future we may want to have an ignore list
    filename = f"{basename}.{_ARCHIVE_FORMAT}"
    with tarfile.open(name=filename, mode=_TAR_FLAGS) as tf:
        for root, dirs, files in os.walk(repository_path):
            for path in _EXCLUDE_PATHS:
                if path in dirs:
                    dirs.remove(path)

            for file in files:
                file_path = os.path.join(root, file)
                tf.add(
                    file_path,
                    arcname=os.path.relpath(file_path, repository_path),
                )
    with open(filename, "rb") as f:
        repository = f.read()
    os.remove(filename)
    return repository


def unpack_workspace(base_dir: str, name: str, repository: bytes):
    workspace_path = os.path.join(base_dir, name)
    filepath = f".tmp.{name}"
    with open(filepath, "wb") as f:
        f.write(repository)
    unpack_archive(filepath, workspace_path, format=_ARCHIVE_FORMAT)

    os.remove(filepath)

    return workspace_path


def add_workspace_config(
    base_dir: str,
    name: str,
    working_directory: str,
    module_name: str,
):
    with open(os.path.join(base_dir, "workspace.yaml"), "a") as ws:
        ws.write(
            (
                "  - python_module:\n"
                f"      module_name: {module_name}\n"
                f"      working_directory: {working_directory}\n"
                f"      executable_path: /opt/venvs/{name}/bin/python\n"
                f"      location_name: {name}\n"
            )
        )


def find_package_entrypoint(file_location):
    if not os.path.isdir(file_location):
        if file_location.endswith(".py"):
            return file_location
        msg = (
            "Entrypoint needs to be a python package or a python file, got: {}"
        ).format(file_location)
        raise ValueError(msg)

    init_file = _find_first_init_file(file_location)
    if init_file is None:
        raise ValueError(
            f"Could not find __init__.py file in directory: {file_location}"
        )
    return init_file


def _find_first_init_file(file_location):
    for root, _, files in os.walk(file_location):
        for file in files:
            if file == "__init__.py":
                return os.path.join(root, file)
