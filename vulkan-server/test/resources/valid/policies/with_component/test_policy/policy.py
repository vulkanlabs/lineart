from enum import Enum

from vulkan_public.spec.component import ComponentInstance, ComponentInstanceConfig
from vulkan_public.spec.dependency import INPUT_NODE, Dependency
from vulkan_public.spec.nodes import BranchNode, TerminateNode
from vulkan_public.spec.policy import PolicyDefinition


class Status(Enum):
    APPROVED = "APPROVED"
    ANALYSIS = "ANALYSIS"
    DENIED = "DENIED"


test_component = ComponentInstance(
    name="test_component",
    version="v0.0.1",
    config=ComponentInstanceConfig(
        name="test_component",
        description="Test Component",
        dependencies={"cpf": Dependency(INPUT_NODE, key="cpf")},
        instance_params={"server_url": "http://fake-url"},
    ),
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
    dependencies={"scores": Dependency("test_component")},
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
    components=[test_component],
    input_schema={"cpf": str, "scr_score": int},
    output_callback=lambda *args, **kwargs: True,
)
