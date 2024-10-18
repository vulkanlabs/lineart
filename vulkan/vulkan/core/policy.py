from typing import Callable

from vulkan_public.spec.component import ComponentInstance
from vulkan_public.spec.nodes import InputNode, Node, TerminateNode
from vulkan_public.spec.policy import POLICY_CONFIG_KEY, PolicyDefinition

from vulkan.core.graph import Graph


class Policy(Graph):
    def __init__(
        self,
        nodes: list[Node],
        input_schema: dict[str, type],
        output_callback: Callable | None = None,
        components: list[ComponentInstance] | None = None,
    ):
        self.output_callback = output_callback
        if output_callback is not None:
            assert callable(output_callback), "Output callback must be a callable"
            nodes = self._with_output_callback(nodes)

        if components is None:
            components = []

        all_nodes = [_make_input_node(input_schema), *nodes, *components]

        self.components = components
        super().__init__(all_nodes, input_schema)

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
    assert (
        POLICY_CONFIG_KEY not in input_schema
    ), f"{POLICY_CONFIG_KEY} is a reserved key"

    input_schema[POLICY_CONFIG_KEY] = dict

    return InputNode(
        name="input_node",
        description="Input node",
        schema=input_schema,
    )
