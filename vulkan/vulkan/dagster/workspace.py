import importlib.util
import os
import sys

from dagster import Definitions, EnvVar, IOManagerDefinition

from vulkan.core.component import ComponentDefinition
from vulkan.core.nodes import InputNode, NodeFactory
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
