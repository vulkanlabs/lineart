import importlib.util
import os
import sys
import tarfile
from shutil import unpack_archive

from dagster import Definitions, EnvVar, IOManagerDefinition

from vulkan.core.component import ComponentDefinition
from vulkan.core.nodes import NodeFactory, InputNode
from vulkan.dagster.component import DagsterComponent
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

    components = []

    for component_instance in policy.components:
        # TODO: DAGSTER_HOME will be available on the server where the code will run,
        # but we should think of a better way to get the path to the component definition.
        DAGSTER_HOME = os.getenv("DAGSTER_HOME")
        base_dir = f"{DAGSTER_HOME}/components"
        # TODO: this alias should be created with a function from the core (as it
        # is used in multiple places)
        alias = f"{component_instance.name}:{component_instance.version}"
        file_location = find_package_entrypoint(os.path.join(base_dir, alias))
        component_definition = extract_component_definition(file_location)
        nodes = configure_component_nodes(
            component_definition.nodes, component_instance.config
        )
        component = DagsterComponent(
            name=component_instance.config["name"],
            description=component_instance.config.get("description", ""),
            nodes=nodes,
            input_schema=component_definition.input_schema,
            dependencies=component_instance.config.get("dependencies", []),
        )
        components.append(component)

    _nodes = [n for n in policy.nodes if not isinstance(n, InputNode)]
    compiled_policy = DagsterPolicy(
        nodes=[*_nodes, *components],
        input_schema=policy.input_schema,
        output_callback=policy.output_callback,
    )

    print([n.name for n in compiled_policy.flattened_nodes])
    print(compiled_policy.flattened_dependencies)

    # By definition, Vulkan dagster worskpaces have a single job.
    jobs = [compiled_policy.to_job(resources)]
    definition = Definitions(
        assets=[],
        jobs=jobs,
        resources={},
    )
    return definition


_ARCHIVE_FORMAT = "gztar"
_TAR_FLAGS = "w:gz"
_EXCLUDE_PATHS = [".git", ".venv", ".vscode"]


def configure_component_nodes(nodes, config):
    _nodes = []
    for node in nodes:
        if isinstance(node, NodeFactory):
            node = node.create(**config["params"])
        _nodes.append(node)
    return _nodes


def extract_component_definition(file_location):
    if not os.path.exists(file_location):
        raise ValueError(f"File not found: {file_location}")

    if os.path.isdir(file_location):
        file_location = os.path.join(file_location, "__init__.py")

    spec = importlib.util.spec_from_file_location("user.component", file_location)
    module = importlib.util.module_from_spec(spec)
    sys.modules["user.component"] = module
    spec.loader.exec_module(module)

    context = vars(module)

    for _, obj in context.items():
        # TODO: validate there is only one component definition
        if isinstance(obj, ComponentDefinition):
            return obj
    raise ValueError("No component definition found in module")


def pack_workspace(name: str, repository_path: str):
    basename = f".tmp.{name}"
    # TODO: In the future we may want to have an ignore list
    filename = f"{basename}.{_ARCHIVE_FORMAT}"
    with tarfile.open(name=filename, mode=_TAR_FLAGS) as tf:
        for root, dirs, files in os.walk(repository_path):
            # TODO: match regex instead of exact path
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
