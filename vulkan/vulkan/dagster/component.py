from vulkan.core.component import ComponentGraph
from vulkan.core.dependency import Dependency
from vulkan.core.nodes import Node, TransformNode, HTTPConnectionNode
from vulkan.dagster.nodes import DagsterNode, Transform, HTTPConnection


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

def to_dagster_nodes(nodes: list[Node]) -> list[DagsterNode]:
    dagster_nodes = []
    for node in nodes:
        if isinstance(node, TransformNode) and not isinstance(node, DagsterNode):
            node = Transform.from_spec(node)
        if isinstance(node, HTTPConnectionNode) and not isinstance(node, DagsterNode):
            node = HTTPConnection.from_spec(node)
        dagster_nodes.append(node)
    return dagster_nodes
