from typing import Any

from vulkan.spec.dependency import Dependency
from vulkan.spec.nodes.base import Node, NodeDefinition, NodeType
from vulkan.spec.nodes.metadata import PolicyNodeMetadata


class PolicyDefinitionNode(Node):
    """A node that represents a policy definition.
    Policy nodes are used to "invoke" policies from within other policies.
    They're used to insert additional metadata for the policy so that it
    can be appropriately connectied to the rest of the workflow.
    """

    def __init__(
        self,
        name: str,
        policy_id: str,
        description: str | None = None,
        dependencies: dict[str, Dependency] | None = None,
    ):
        super().__init__(
            name=name,
            description=description,
            typ=NodeType.POLICY,
            dependencies=dependencies,
        )
        self.policy_id = policy_id

    def node_definition(self) -> NodeDefinition:
        metadata = PolicyNodeMetadata(policy_id=self.policy_id)
        return NodeDefinition(
            name=self.name,
            description=self.description,
            node_type=self.type.value,
            dependencies=self.dependencies,
            metadata=metadata,
        )

    @classmethod
    def from_dict(cls, spec: dict[str, Any]) -> "PolicyDefinitionNode":
        definition = NodeDefinition.from_dict(spec)
        if definition.node_type != NodeType.POLICY.value:
            raise ValueError(f"Expected NodeType.POLICY, got {definition.node_type}")
        if definition.metadata is None or definition.metadata.policy_id is None:
            raise ValueError("Missing policy metadata")

        return cls(
            name=definition.name,
            description=definition.description,
            dependencies=definition.dependencies,
            policy_id=definition.metadata.policy_id,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "node_type": self.type.value,
            "description": self.description,
            "dependencies": self.dependencies,
            "metadata": {
                "policy_definition": self.policy_id,
            },
        }
