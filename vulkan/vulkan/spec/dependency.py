from dataclasses import dataclass
from typing import TypedDict


class DependencyDict(TypedDict):
    """Dict representation of a Dependency object."""

    node: str
    output: str | None = None
    key: str | None = None
    hierarchy: list[str] | None = None


@dataclass
class Dependency:
    """Allows the user to qualify the dependency between two nodes.

    A dependency may be defined in three ways:
    1. When a single string is passed, it is assumed that the dependency is
         the entire output of the node with the same name.
    2. When node and output are specified, we interpret that the dependency
        is on the `output` product of `node`. This is currently only used
        in branching nodes, where the user can specify which output to use.
        That is, if a branch has two possible outputs (eg left and right),
        the user can specify which one to use as
        `Dependency(node="branch", output="left")`.
    3. When key is specified, the dependency is on the `key` entry of the
        given node. This allows the user to access an internal dictionary
        entry of the node, which can simplify data retrieval.
        Note that this will break if the node does not return a dictionary.

    An example of each scenario:

    ```
    x: Dependency("node")  # Depends on the entire output of "node"
    x: Dependency(node="node", output="condition")  # Depends on "node.condition"
    x: Dependency(node="node", key="key")  # Depends on "node['key']"
    ```

    """

    node: str
    output: str | None = None
    key: str | None = None
    hierarchy: list[str] | None = None

    def __post_init__(self):
        assert isinstance(self.node, str) and len(self.node) > 0, (
            "Node name must be a non-empty string"
        )

        assert self.output is None or self.key is None, (
            "Cannot specify both output and key at the moment"
        )

    @property
    def id(self) -> str:
        """The ID of the dependency.

        This is the full path to the dependency, including the hierarchy.
        """
        hierarchy = "-".join(self.hierarchy) if self.hierarchy is not None else ""

        str_repr = self.node
        if len(hierarchy) > 0:
            str_repr = f"{hierarchy}.{self.node}"

        return str_repr

    def __str__(self) -> str:
        node_id = self.id

        if self.output is not None:
            return node_id + f".{self.output}"
        if self.key is not None:
            return node_id + f"[{self.key}]"
        return node_id

    @classmethod
    def from_dict(cls, data: DependencyDict) -> "Dependency":
        return cls(
            node=data["node"],
            output=data["output"],
            key=data["key"],
            hierarchy=data.get("hierarchy"),
        )

    def to_dict(self) -> DependencyDict:
        return DependencyDict(
            node=self.node,
            output=self.output,
            key=self.key,
            hierarchy=self.hierarchy,
        )


INPUT_NODE = "input_node"
"""Name of the input node of a subgraph. Always created internally."""
