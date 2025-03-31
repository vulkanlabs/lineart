from enum import Enum

from vulkan_public.spec.component import ComponentInstance, ComponentInstanceConfig
from vulkan_public.spec.dependency import INPUT_NODE, Dependency
from vulkan_public.spec.nodes.base import BranchNode, TerminateNode
from vulkan_public.spec.policy import PolicyDefinition

DATA_SERVER_URL = "http://testdata:5000"
CLIENT_SERVER_URL = "http://echo:80/post"

http_params = dict(method="GET", headers={}, params={})


class Status(Enum):
    APPROVED = "APPROVED"
    ANALYSIS = "ANALYSIS"
    DENIED = "DENIED"


vendor_data = ComponentInstance(
    name="vendor_data",
    version="v0.0.1",
    config=ComponentInstanceConfig(
        name="vendor_data_request",
        description="Get Vendor API data",
        dependencies={"cpf": Dependency(INPUT_NODE, key="cpf")},
    ),
)


def branch_condition_1(context, scores, **kwargs):
    context.log.info(f"Scores: {scores} ({type(scores)})")
    if scores["scr"] > 600:
        return "approved"
    if scores["serasa"] > 800:
        return "analysis"
    return "denied"


branch_1 = BranchNode(
    func=branch_condition_1,
    name="branch_1",
    description="BranchNode data",
    dependencies={"scores": Dependency(vendor_data.config.name)},
    choices=["approved", "analysis", "denied"],
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
    components=[vendor_data],
    input_schema={"cpf": str},
)
