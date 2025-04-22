from enum import Enum

import vapeplot
from vulkan_public.spec.dependency import INPUT_NODE, Dependency
from vulkan_public.spec.nodes import BranchNode, TerminateNode
from vulkan_public.spec.policy import PolicyDefinition


class Status(Enum):
    APPROVED = "APPROVED"
    ANALYSIS = "ANALYSIS"
    DENIED = "DENIED"


# Branching node
def branch_condition_1(context, scores, **kwargs):
    context.log.info(f"BranchNode: {vapeplot.__dir__()}")
    if scores["scr_score"] > 800:
        return "approved"
    if scores["scr_score"] > 500:
        return "analysis"
    return "denied"


branch_1 = BranchNode(
    func=branch_condition_1,
    name="branch_1",
    description="BranchNode data",
    dependencies={"scores": Dependency(INPUT_NODE)},
    outputs=["approved", "analysis", "denied"],
)

approved = TerminateNode(
    name="approved",
    description="TerminateNode data branch",
    return_status=Status.APPROVED,
    dependencies={"condition": Dependency("branch_1", "approved")},
)

analysis = TerminateNode(
    name="analysis",
    description="TerminateNode data branch",
    return_status=Status.ANALYSIS,
    dependencies={"condition": Dependency("branch_1", "analysis")},
)

denied = TerminateNode(
    name="denied",
    description="TerminateNode data branch",
    return_status=Status.DENIED,
    dependencies={"condition": Dependency("branch_1", "denied")},
)


demo_policy = PolicyDefinition(
    nodes=[
        branch_1,
        approved,
        analysis,
        denied,
    ],
    components=[],
    input_schema={"cpf": str, "scr_score": int},
    output_callback=lambda *args, **kwargs: True,
)
