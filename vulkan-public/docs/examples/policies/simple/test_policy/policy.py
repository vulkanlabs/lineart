from enum import Enum

from vulkan_public.spec.dependency import INPUT_NODE, Dependency
from vulkan_public.spec.nodes.base import BranchNode, TerminateNode
from vulkan_public.spec.policy import PolicyDefinition


class Status(Enum):
    APPROVED = "APPROVED"
    DENIED = "DENIED"


# Branching node
def branch_condition(context, inputs, **kwargs):
    context.log.info(inputs)
    if inputs["score"] > context.env.get("MINIMUM_SCORE"):
        return "approved"
    return "denied"


branch = BranchNode(
    func=branch_condition,
    name="branch",
    description="Make a decision based on the data source",
    dependencies={
        "inputs": Dependency(INPUT_NODE),
    },
    choices=["approved", "denied"],
)

approved = TerminateNode(
    name="approved",
    description="Approve customer based on the score",
    return_status="APPROVED",
    dependencies={"condition": Dependency("branch", "approved")},
)

denied = TerminateNode(
    name="denied",
    description="Deny customers that are below minimum",
    return_status="DENIED",
    dependencies={"condition": Dependency("branch", "denied")},
)

demo_policy = PolicyDefinition(
    nodes=[
        branch,
        approved,
        denied,
    ],
    components=[],
    config_variables=["MINIMUM_SCORE"],
    input_schema={"tax_id": str, "score": int},
)
