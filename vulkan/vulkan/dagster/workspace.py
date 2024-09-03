import os

from dagster import Definitions, EnvVar, IOManagerDefinition

from vulkan.core.component import (
    ComponentDefinition,
    ComponentGraph,
    check_all_parameters_specified,
)
from vulkan.core.policy import Policy, PolicyDefinition
from vulkan.dagster.io_manager import (
    DB_CONFIG_KEY,
    PUBLISH_IO_MANAGER_KEY,
    DBConfig,
    metadata_io_manager,
    postgresql_io_manager,
)
from vulkan.dagster.policy import DagsterFlow
from vulkan.dagster.run_config import RUN_CONFIG_KEY, VulkanRunConfig
from vulkan.environment.packing import find_definitions, find_package_entrypoint


def make_workspace_definition(
    file_location: str,
    components_base_dir: str,
) -> Definitions:
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
    print([n.name for n in dagster_flow.nodes])
    print(dagster_flow.dependencies)
    # By definition, Vulkan dagster worskpaces have a single job.
    jobs = [dagster_flow.to_job(resources)]
    definition = Definitions(
        assets=[],
        jobs=jobs,
        resources={},
    )
    return definition


def resolve_policy(file_location: str, components_base_dir: str) -> Policy:
    policy_defs = find_definitions(file_location, PolicyDefinition)
    if len(policy_defs) != 1:
        raise ValueError(
            f"Expected only one PolicyDefinition in the module, found {len(policy_defs)}"
        )
    policy_def: PolicyDefinition = policy_defs[0]

    # TODO: We're not handling installing the component packages.
    # This will lead to errors if components have dependencies.
    components = []
    for component_instance in policy_def.components:
        alias = component_instance.alias()
        file_location = find_package_entrypoint(
            os.path.join(components_base_dir, alias)
        )
        component_definition = extract_component_definition(file_location)

        check_all_parameters_specified(component_definition, component_instance)
        component = ComponentGraph.from_spec(component_definition, component_instance)
        components.append(component)

    policy = Policy(
        policy_def.nodes,
        policy_def.input_schema,
        policy_def.output_callback,
        components,
    )
    return policy


def extract_component_definition(file_location):
    definitions = find_definitions(file_location, ComponentDefinition)
    if len(definitions) == 1:
        return definitions[0]
    msg = f"Expected only one component definition, found {len(definitions)} in module"
    raise ValueError(msg)


def add_workspace_config(
    base_dir: str,
    name: str,
    working_directory: str,
    module_name: str,
):
    with open(os.path.join(base_dir, "workspace.yaml"), "a") as ws:
        init_path = os.path.join(working_directory, "__init__.py")
        ws.write(
            (
                "  - python_file:\n"
                # f"      module_name: {module_name}\n"
                f"      relative_path: {init_path}\n"
                f"      working_directory: {working_directory}\n"
                f"      executable_path: /opt/venvs/{name}/bin/python\n"
                f"      location_name: {name}\n"
            )
        )
