from typing import Any, cast

from vulkan.spec.dependency import Dependency
from vulkan.spec.nodes.base import Node, NodeDefinition, NodeType
from vulkan.spec.nodes.metadata import (
    DecisionCondition,
    DecisionNodeMetadata,
    DecisionType,
)


class DecisionNode(Node):
    """A node that performs branching logic in the DAG.

    Decision nodes are used to evaluate a set of conditions and use the
    result to determine the next steps in the workflow.
    Conditions are specified as branches of an if-else tree.
    All Decision nodes must have at least an `if` and an `else` condition.
    Each condition will map to a specific output, and should be specified
    as a Jinja2 template string.
    """

    def __init__(
        self,
        name: str,
        conditions: list[DecisionCondition],
        dependencies: dict[str, Dependency],
        description: str | None = None,
        hierarchy: list[str] | None = None,
    ):
        """Perform branching logic in the DAG.

        Parameters
        ----------
        name : str
            The name of the node.
        conditions : list[DecisionCondition]
            A list of conditions to evaluate.
        description : str, optional
            A description of the node. Used for documentation purposes and
            shown in the user interface.
        hierarchy : list[str], optional
        """
        super().__init__(
            name=name,
            description=description,
            typ=NodeType.DECISION,
            dependencies=dependencies,
            hierarchy=hierarchy,
        )
        self.conditions = conditions
        if len(conditions) == 0:
            raise ValueError("DecisionNode must have at least one condition")
        has_if = any(
            condition.decision_type == DecisionType.IF for condition in conditions
        )
        if not has_if:
            raise ValueError("DecisionNode must have an `if` condition")
        has_else = any(
            condition.decision_type == DecisionType.ELSE for condition in conditions
        )
        if not has_else:
            raise ValueError("DecisionNode must have an `else` condition")

    @classmethod
    def from_dict(cls, spec: dict[str, Any]) -> "DecisionNode":
        definition = NodeDefinition.from_dict(spec)
        if definition.metadata is None:
            raise ValueError(f"Metadata not set for node {definition.name}")
        metadata = cast(DecisionNodeMetadata, definition.metadata)
        return cls(
            name=definition.name,
            conditions=metadata.conditions,
            dependencies=definition.dependencies,
            description=definition.description,
        )

    def node_definition(self) -> NodeDefinition:
        return NodeDefinition(
            name=self.name,
            node_type=self.type.value,
            metadata=DecisionNodeMetadata(conditions=self.conditions),
            dependencies=self.dependencies,
            description=self.description,
            hierarchy=self.hierarchy,
        )
