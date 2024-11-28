import json
from enum import Enum

from vulkan_public.spec.dependency import INPUT_NODE, Dependency
from vulkan_public.spec.nodes import (
    BranchNode,
    DataInputNode,
    TerminateNode,
    TransformNode,
)
from vulkan_public.spec.policy import PolicyDefinition

DATA_SERVER_URL = "http://testdata:5000"
CLIENT_SERVER_URL = "http://echo:80/post"

http_params = dict(method="GET", headers={}, params={})


class Status(Enum):
    APPROVED = "APPROVED"
    ANALYSIS = "ANALYSIS"
    DENIED = "DENIED"


body = TransformNode(
    func=lambda inputs: {"tax_id": inputs["cpf"]},
    name="body",
    description="Serasa body",
    dependencies={"inputs": Dependency(INPUT_NODE)},
)

get_data = DataInputNode(
    name="vendor_api_data",
    description="Get data from Vendor API",
    source="vendor-name:api-name:v0.0.1",
    dependencies={"body": Dependency(body.name)},
    process_fn=...,
)


def load_data(context, raw_data, **kwargs):
    context.log.info(f"Raw data: {raw_data}")
    data = json.loads(raw_data)
    context.log.info(f"Data loaded: {data} ({type(data)})")
    return data


process_data = TransformNode(
    func=load_data,
    name="post_process_data",
    description="Post process data",
    dependencies={"raw_data": Dependency(get_data.name)},
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
    dependencies={"scores": Dependency(process_data.name)},
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
        body,
        get_data,
        process_data,
        branch_1,
        approved,
        analysis,
        denied,
    ],
    input_schema={"cpf": str},
)
