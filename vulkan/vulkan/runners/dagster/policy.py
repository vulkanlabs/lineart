import requests
from dagster import (
    ConfigurableResource,
    DependencyDefinition,
    GraphDefinition,
    HookContext,
    OpDefinition,
    failure_hook,
)

from vulkan.core.run import RunStatus
from vulkan.runners.dagster.io_manager import DB_CONFIG_KEY, POSTGRES_IO_MANAGER_KEY
from vulkan.runners.dagster.names import normalize_node_id
from vulkan.runners.dagster.nodes import to_dagster_nodes
from vulkan.runners.dagster.run_config import RUN_CONFIG_KEY
from vulkan.spec.dependency import Dependency
from vulkan.spec.nodes import Node

DEFAULT_POLICY_NAME = "default_policy"


class DagsterFlow:
    def __init__(self, nodes: list[Node]) -> None:
        self.nodes = to_dagster_nodes(nodes)
        self.dependencies = _extract_dependencies(self.nodes)

    def to_job(self, resources: dict[str, ConfigurableResource]):
        g = self._graph()
        return g.to_job(
            resource_defs=resources,
            hooks={_notify_failure},
        )

    def _graph(self):
        ops = self._dagster_ops()
        return GraphDefinition(
            name=DEFAULT_POLICY_NAME,
            node_defs=ops,
            dependencies=self.dependencies,
        )

    def _dagster_ops(self) -> list[OpDefinition]:
        nodes = []
        for node in self.nodes:
            dagster_node = node.op()
            if _accesses_internal_resources(dagster_node):
                msg = f"Policy node {node.name} tried to access protected resources"
                raise ValueError(msg)
            nodes.append(dagster_node)
        return nodes


@failure_hook(required_resource_keys={RUN_CONFIG_KEY})
def _notify_failure(context: HookContext) -> bool:
    vulkan_run_config = context.resources.vulkan_run_config
    server_url = vulkan_run_config.server_url
    run_id = vulkan_run_config.run_id

    context.log.debug(f"Notifying failure for run {run_id}")
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


def _accesses_internal_resources(op: OpDefinition) -> bool:
    INTERNAL_RESOURCE_KEYS = {DB_CONFIG_KEY, POSTGRES_IO_MANAGER_KEY, "io_manager"}
    return len(INTERNAL_RESOURCE_KEYS.intersection(op.required_resource_keys)) > 0


def _extract_dependencies(nodes: list[Node]) -> dict[str, dict[str, Dependency]]:
    return {
        node.name: _as_dagster_dependencies(node.dependencies)
        for node in nodes
        if len(node.dependencies) > 0
    }


def _as_dagster_dependencies(
    dependencies: dict[str, Dependency] | None,
) -> dict[str, DependencyDefinition]:
    if dependencies is None:
        return None

    deps = {}
    for k, v in dependencies.items():
        # Check if the dependency specifies an output name
        if v.output is not None:
            definition = DependencyDefinition(normalize_node_id(v.id), v.output)
        else:
            definition = DependencyDefinition(normalize_node_id(v.id), "result")
        deps[normalize_node_id(k)] = definition
    return deps
