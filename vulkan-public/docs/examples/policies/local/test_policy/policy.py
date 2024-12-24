from enum import Enum

from vulkan_public.spec.dependency import INPUT_NODE, Dependency
from vulkan_public.spec.nodes import BranchNode, DataInputNode, TerminateNode
from vulkan_public.spec.policy import PolicyDefinition


class Status(Enum):
    APPROVED = "APPROVED"
    DENIED = "DENIED"


sample_api = DataInputNode(
    name="sample_api",
    description="DataInputNode data",
    source="vendor-name:api-name:v0.0.1",
    dependencies={"inputs": Dependency(INPUT_NODE)},
)


approved = TerminateNode(
    name="approved",
    description="TerminateNode data branch",
    return_status=Status.APPROVED,
    dependencies={"condition": Dependency("branch_1", "approved")},
)


denied = TerminateNode(
    name="denied",
    description="TerminateNode data branch",
    return_status=Status.DENIED,
    dependencies={"condition": Dependency("branch_1", "denied")},
)


# Branching node
def branch_condition_1(context, scores, **kwargs):
    context.log.info(f"BranchNode data: {scores}")
    if scores["score"] > context.env.get("SCORE_CUTOFF", 500):
        return "approved"
    return "denied"


branch_1 = BranchNode(
    func=branch_condition_1,
    name="branch_1",
    description="BranchNode data",
    dependencies={"scores": Dependency(sample_api.name)},
    outputs=["approved", "denied"],
)

demo_policy = PolicyDefinition(
    nodes=[
        sample_api,
        branch_1,
        approved,
        denied,
    ],
    components=[],
    config_variables=["SCORE_CUTOFF"],
    input_schema={"tax_id": str, "score": int},
)
