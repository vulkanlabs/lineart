from enum import Enum

from vulkan.spec.component import ComponentInstance, ComponentInstanceConfig
from vulkan.spec.dependency import INPUT_NODE, Dependency
from vulkan.spec.nodes import BranchNode, TerminateNode, TransformNode
from vulkan.spec.policy import PolicyDefinition


class Status(Enum):
    APPROVED = "APPROVED"
    ANALYSIS = "ANALYSIS"
    DENIED = "DENIED"


scr_component = ComponentInstance(
    name="non_existing_component",
    version="v0.0.1",
    config=ComponentInstanceConfig(
        name="scr_query_component",
        description="Get SCR score",
        dependencies={"cpf": Dependency(INPUT_NODE, key="cpf")},
        instance_params={"server_url": "http://fake-url/scr"},
    ),
)


def join_func(context, scr_score, **kwargs):
    scores = {"scr_score": scr_score}
    return scores


join_transform = TransformNode(
    func=join_func,
    name="join_transform",
    description="Join scores",
    dependencies={"scr_score": Dependency("scr_query_component")},
)


def branch_condition_1(context, scores, **kwargs):
    if scores["scr_score"] > 800:
        return "approved"
    if scores["scr_score"] > 500:
        return "analysis"
    return "denied"


branch_1 = BranchNode(
    func=branch_condition_1,
    name="branch_1",
    description="BranchNode data",
    dependencies={"scores": Dependency("join_transform")},
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
        join_transform,
        branch_1,
        approved,
        analysis,
        denied,
    ],
    components=[scr_component],
    input_schema={"cpf": str, "scr_score": int},
    output_callback=lambda *args, **kwargs: True,
)
