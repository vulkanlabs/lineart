from typing import Any

from ..core.component import ComponentGraph
from ..core.nodes import Node
from .nodes import Transform


class Component(ComponentGraph):

    def __init__(
        self,
        name: str,
        description: str,
        nodes: list[Node],
        input_schema: dict[str, type],
        dependencies: dict[str, Any],
    ):
        all_nodes = [_make_input_node(name, dependencies), *nodes]
        super().__init__(name, description, all_nodes, input_schema, dependencies)


def _make_input_node(name: str, dependencies: dict[str, Any]) -> list[Node]:
    return Transform(
        name=ComponentGraph.make_input_node_name(name),
        description=f"Input node for Component {name}",
        func=lambda _, **kwargs: {k: kwargs[k] for k in dependencies.keys()},
        dependencies=dependencies,
    )
