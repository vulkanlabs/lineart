from typing import Any

import requests
from dagster import (
    ConfigurableResource,
    DependencyDefinition,
    GraphDefinition,
    HookContext,
    OpDefinition,
    failure_hook,
)

from vulkan_dagster.core.graph import Policy
from vulkan_dagster.core.dependency import Dependency
from vulkan_dagster.core.run import RunStatus
from .io_manager import DB_CONFIG_KEY, POSTGRES_IO_MANAGER_KEY
from .nodes import Input
from .run_config import RUN_CONFIG_KEY

DEFAULT_POLICY_NAME = "default_policy"


class DagsterPolicy(Policy):
    def __init__(
        self,
        nodes: list,
        input_schema: dict[str, type],
        output_callback: callable,
    ):
        internal_nodes = self._internal_nodes(input_schema)
        all_nodes = [*internal_nodes, *nodes]
        super().__init__(all_nodes, input_schema, output_callback)

    def graph(self):
        nodes = self._dagster_nodes()
        deps = self._graph_dependencies()
        return GraphDefinition(
            name=DEFAULT_POLICY_NAME,
            node_defs=nodes,
            dependencies=deps,
        )

    def _dagster_nodes(self) -> list[OpDefinition]:
        nodes = []
        for node in self.flattened_nodes:
            dagster_node = node.op()
            if _accesses_internal_resources(dagster_node):
                msg = f"Policy node {node.name} tried to access protected resources"
                raise ValueError(msg)
            nodes.append(dagster_node)
        return nodes

    def _graph_dependencies(self):
        return {
            node.name: _as_dagster_dependencies(node.dependencies)
            for node in self.flattened_nodes
            if len(node.dependencies) > 0
        }

    def to_job(self, resources: dict[str, ConfigurableResource]):
        return self.graph().to_job(
            resource_defs=resources,
            hooks={_notify_failure},
        )

    def _internal_nodes(self, input_schema) -> list:
        return [
            self._input_node(input_schema),
        ]

    def _input_node(self, input_schema) -> Input:
        return Input(
            name="input_node",
            description="Input node",
            schema=input_schema,
        )



@failure_hook(required_resource_keys={RUN_CONFIG_KEY})
def _notify_failure(context: HookContext) -> bool:
    vulkan_run_config = context.resources.vulkan_run_config
    server_url = vulkan_run_config.server_url
    run_id = vulkan_run_config.run_id

    context.log.info(f"Notifying failure for run {run_id}")
    url = f"{server_url}/runs/{run_id}"
    dagster_run_id: str = context.run_id
    result = requests.put(
        url,
        json={
            "result": "",
            "status": RunStatus.FAILURE.value,
        },
    )
    if result.status_code not in {200, 204}:
        msg = f"Error {result.status_code} Failed to notify failure to {url} for run {dagster_run_id}"
        context.log.error(msg)


# TODO: should we do something like this?
def _accesses_internal_resources(op: OpDefinition) -> bool:
    INTERNAL_RESOURCE_KEYS = {DB_CONFIG_KEY, POSTGRES_IO_MANAGER_KEY, "io_manager"}
    return len(INTERNAL_RESOURCE_KEYS.intersection(op.required_resource_keys)) > 0


def _as_dagster_dependencies(
    dependencies: dict[str, Dependency] | None
) -> dict[str, DependencyDefinition]:
    if dependencies is None:
        return None

    deps = {}
    for k, v in dependencies.items():
        # Check if the dependency specifies an output name or a key
        if v.output is not None:
            definition = DependencyDefinition(v.node, v.output)
        else:
            definition = DependencyDefinition(v.node, "result")
        deps[k] = definition
    return deps
