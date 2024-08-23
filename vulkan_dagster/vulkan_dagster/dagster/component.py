from vulkan_dagster.core.component import ComponentGraph
from vulkan_dagster.core.dependency import Dependency
from vulkan_dagster.core.nodes import Node

from vulkan_dagster.dagster.nodes import Transform


class Component(ComponentGraph):

    def __init__(
        self,
        name: str,
        description: str,
        nodes: list[Node],
        input_schema: dict[str, type],
        dependencies: dict[str, Dependency],
    ):
        all_nodes = [_make_input_node(name, dependencies), *nodes]
        super().__init__(name, description, all_nodes, input_schema, dependencies)


def _make_input_node(name: str, dependencies: dict[str, Dependency]) -> list[Node]:
    def _input_fn(_, **kwargs: dict):
        inputs = {}
        for k, v in dependencies.items():
            if k not in kwargs.keys():
                raise ValueError(f"Missing input {k}")
            if v.key is not None:
                inputs[k] = kwargs[k][v.key]
            else:
                inputs[k] = kwargs[k]

        return inputs

    return Transform(
        name=ComponentGraph.make_input_node_name(name),
        description=f"Input node for Component {name}",
        func=_input_fn,
        dependencies=dependencies,
        hidden=True,
    )
