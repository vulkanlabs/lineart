from dataclasses import dataclass, field

from vulkan.core.component import ComponentInstance
from vulkan.core.dependency import INPUT_NODE
from vulkan.core.graph import Graph
from vulkan.core.nodes import InputNode, Node, TerminateNode


@dataclass
class PolicyDefinition:
    nodes: list[Node]
    input_schema: dict[str, type]
    output_callback: callable
    components: list[ComponentInstance] = field(default_factory=list)

    def __post_init__(self):
        if not callable(self.output_callback):
            raise ValueError("Output callback must be a callable")

        self._validate_node_dependencies()

    def _validate_node_dependencies(self):
        nodes = {node.name: node.dependencies for node in self.nodes}
        nodes.update({c.config.name: c.config.dependencies for c in self.components})

        for node_name, dependencies in nodes.items():
            if dependencies is None:
                continue
            for dep in dependencies.values():
                if dep.node == INPUT_NODE:
                    # Input nodes are added to the graph after validation.
                    continue

                if dep.node not in nodes.keys():
                    msg = (
                        f"Node {node_name} has a dependency {dep.node} "
                        "that is not in the graph"
                    )
                    raise ValueError(msg)


class Policy(Graph):
    def __init__(
        self,
        nodes: list[Node],
        input_schema: dict[str, type],
        output_callback: callable,
        components: list[ComponentInstance] = field(default_factory=list),
    ):
        assert callable(output_callback), "Output callback must be a callable"
        self.output_callback = output_callback
        nodes = self._with_output_callback(nodes)
        all_nodes = [_make_input_node(input_schema), *nodes]

        super().__init__(all_nodes, input_schema)
        self.components = components

    def _with_output_callback(self, nodes: list[Node]) -> list[Node]:
        modified_nodes = []
        for node in nodes:
            if isinstance(node, TerminateNode):
                node = node.with_callback(self.output_callback)
            modified_nodes.append(node)

        return modified_nodes

    @classmethod
    def from_definition(cls, definition: PolicyDefinition) -> "Policy":
        return cls(
            nodes=definition.nodes,
            input_schema=definition.input_schema,
            output_callback=definition.output_callback,
            components=definition.components,
        )


def _make_input_node(input_schema) -> InputNode:
    return InputNode(
        name="input_node",
        description="Input node",
        schema=input_schema,
    )
