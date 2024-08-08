from inspect import getsource

import requests
from dagster import (
    ConfigurableResource,
    GraphDefinition,
    HookContext,
    OpDefinition,
    failure_hook,
)

from .io_manager import DB_CONFIG_KEY, POSTGRES_IO_MANAGER_KEY
from .nodes import Input, Node, NodeType, Terminate, VulkanNodeDefinition
from .run import RUN_CONFIG_KEY, RunStatus


class Policy:
    def __init__(
        self,
        name: str,
        description: str,
        nodes: list[Node],
        input_schema: dict[str, type],
        output_callback: callable,
    ):
        assert len(nodes) > 0, "Policy must have at least one node"
        assert all(
            isinstance(n, Node) for n in nodes
        ), "All elements must be of type Node"
        assert all(
            isinstance(k, str) and isinstance(v, type) for k, v in input_schema.items()
        ), "Input schema must be a dictionary of str -> type"
        assert callable(output_callback), "Output callback must be a callable"

        self.name = name
        self.description = description
        self.input_schema = input_schema
        self.output_callback = output_callback

        internal_nodes = self._internal_nodes()
        self.nodes = self._update_nodes(nodes, internal_nodes)

    def graph(self):
        nodes = self._dagster_nodes()
        deps = self._graph_dependencies()
        return GraphDefinition(
            name=self.name,
            description=self.description,
            node_defs=nodes,
            dependencies=deps,
        )

    def node_definitions(self) -> dict[str, VulkanNodeDefinition]:
        definitions = {}
        for node in self.nodes:
            opt_args = {}
            dagster_deps = node.graph_dependencies()
            if node.graph_dependencies() is not None:
                opt_args["dependencies"] = [v.node for k, v in dagster_deps.items()]
            if node.type == NodeType.TRANSFORM or node.type == NodeType.BRANCH:
                opt_args["metadata"] = {"executable": getsource(node.func)}

            definitions[node.name] = VulkanNodeDefinition(
                name=node.name,
                description=node.description,
                node_type=node.type.value,
                **opt_args,
            )
        return definitions

    def _dagster_nodes(self) -> list[OpDefinition]:
        nodes = []
        for node in self.nodes:
            dagster_node = node.node()
            if _accesses_internal_resources(dagster_node):
                msg = f"Policy node {node.name} tried to access protected resources"
                raise ValueError(msg)
            nodes.append(dagster_node)
        return nodes

    def _graph_dependencies(self):
        return {
            n.name: n.graph_dependencies()
            for n in self.nodes
            if len(n.dependencies) > 0
        }

    def to_job(self, resources: dict[str, ConfigurableResource]):
        return self.graph().to_job(
            self.name,
            resource_defs=resources,
            hooks={_notify_failure},
        )

    def _internal_nodes(self) -> list[Node]:
        return [
            self._input_node(),
        ]

    def _input_node(self) -> Input:
        return Input(
            name="input_node",
            description="Input node",
            config_schema=self.input_schema,
        )

    def _update_nodes(self, nodes, internal_nodes):
        all_nodes = [*internal_nodes]
        for node in nodes:
            if isinstance(node, Terminate):
                node = node.with_callback(self.output_callback)
            all_nodes.append(node)

        return all_nodes


@failure_hook(required_resource_keys={RUN_CONFIG_KEY})
def _notify_failure(context: HookContext) -> bool:
    vulkan_run_config = context.resources.vulkan_run_config
    server_url = vulkan_run_config.server_url
    policy_id = vulkan_run_config.policy_id
    run_id = vulkan_run_config.run_id

    context.log.info(f"Notifying failure for run {run_id} in policy {policy_id}")
    # TODO: get URL from env config
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
