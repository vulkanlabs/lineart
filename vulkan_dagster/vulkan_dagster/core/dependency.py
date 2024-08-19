from dataclasses import dataclass


@dataclass
class Dependency:
    """Allows the user to qualify the dependency between two nodes.

    A dependency may be defined in three ways:
    1. When a single string is passed, it is assumed that the dependency is
         the entire output of the node with the same name.
    2. When node and output are specified, we interpret that the dependency
        is on the `output` product of `node`.
    3. When key is specified, the dependency is on the `key` entry of the
        given node. This allows the user to access an internal dictionary
        entry of the node, which can simplify data retrieval.
    """

    node: str
    output: str | None = None
    key: str | None = None

    def __post_init__(self):
        assert (
            isinstance(self.node, str) and len(self.node) > 0
        ), "Node name must be a non-empty string"

        assert (
            self.output is None or self.key is None
        ), "Cannot specify both output and key at the moment"

    def __str__(self) -> str:
        if self.output is not None:
            return f"{self.node}.{self.output}"
        if self.key is not None:
            return f"{self.node}[{self.key}]"
        return self.node
