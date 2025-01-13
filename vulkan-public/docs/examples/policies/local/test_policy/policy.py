from enum import Enum

from vulkan_public.spec.dependency import INPUT_NODE, Dependency
from vulkan_public.spec.nodes import BranchNode, DataInputNode, TerminateNode
from vulkan_public.spec.policy import PolicyDefinition

sample_file_input = DataInputNode(
    name="sample_file_input",
    description="DataInputNode with File Input",
    source="file-input:my-api-name:v0.0.1",
    dependencies={"inputs": Dependency(INPUT_NODE)},
)


# Branching node
def branch_condition(context, scores, **kwargs):
    context.log.info(scores)
    if scores["score"] > context.env.get("SCORE_CUTOFF"):
        return "approved"
    return "denied"


branch = BranchNode(
    func=branch_condition,
    name="branch",
    description="BranchNode data",
    dependencies={
        "scores": Dependency(sample_file_input.name),
    },
    outputs=["approved", "denied"],
)

approved = TerminateNode(
    name="approved",
    description="TerminateNode data branch",
    return_status="APPROVED",
    dependencies={"condition": Dependency("branch", "approved")},
)

denied = TerminateNode(
    name="denied",
    description="TerminateNode data branch",
    return_status="DENIED",
    dependencies={"condition": Dependency("branch", "denied")},
)

demo_policy = PolicyDefinition(
    nodes=[
        sample_file_input,
        branch,
        approved,
        denied,
    ],
    components=[],
    config_variables=["SCORE_CUTOFF"],
    input_schema={"tax_id": str},
)
