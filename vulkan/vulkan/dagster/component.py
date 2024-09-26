from vulkan.core.component import ComponentGraph
from vulkan.dagster.nodes import to_dagster_nodes
from vulkan.spec.dependency import Dependency
from vulkan.spec.nodes import Node


class DagsterComponent(ComponentGraph):
    def __init__(
        self,
        name: str,
        description: str,
        nodes: list[Node],
        input_schema: dict[str, type],
        dependencies: dict[str, Dependency],
    ):
        super().__init__(name, description, nodes, input_schema, dependencies)
        self._nodes = to_dagster_nodes(self.nodes)
        self._flattened_nodes = to_dagster_nodes(self._flattened_nodes)
