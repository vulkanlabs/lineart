import os
from functools import partial

import requests
from dagster import OpExecutionContext
from dotenv import dotenv_values

from vulkan_dagster.nodes import (
    Branch,
    HTTPConnection,
    Policy,
    Status,
    Terminate,
    Transform,
)

CONFIG = dotenv_values()
DATA_SERVER_URL = f"http://127.0.0.1:{CONFIG['TEST_DATA_SERVER_PORT']}"
CLIENT_SERVER_URL = f"http://127.0.0.1:{CONFIG['TEST_CLIENT_SERVER_PORT']}"

http_params = dict(method="GET", headers={}, params={})

scr_body = Transform(
    func=lambda _, inputs: {"cpf": inputs["cpf"]},
    name="scr_body",
    description="SCR body",
    params={"inputs": "input_node"},
)
scr = HTTPConnection(
    name="scr",
    description="Get SCR score",
    url=f"{DATA_SERVER_URL}/scr",
    dependencies={"body": "scr_body"},
    **http_params,
)


serasa_body = Transform(
    func=lambda _, inputs: {"cpf": inputs["cpf"]},
    name="serasa_body",
    description="Serasa body",
    params={"inputs": "input_node"},
)
serasa = HTTPConnection(
    name="serasa",
    description="Get Serasa score",
    url=f"{DATA_SERVER_URL}/serasa",
    dependencies={"body": "serasa_body"},
    **http_params,
)


# The user function needs to use a set of parameters
# that is defined by previous ops (validated in dagster).
# It also needs to take the context and **kwargs.
def scr_func(context, scr_response, **kwargs):
    context.log.info(f"Received SCR: {scr_response}")
    score = scr_response["score"]
    return score


scr_transform = Transform(
    func=scr_func,
    params={"scr_response": "scr"},
    name="scr_transform",
    description="Transform SCR data",
)


def serasa_func(context, serasa_response, **kwargs):
    context.log.info(f"Received Serasa: {serasa_response}")
    score = 2 * serasa_response["score"] ** -1
    context.log.warning(f"Transformed Serasa: {score}")
    return score


serasa_transform = Transform(
    func=serasa_func,
    name="serasa_transform",
    description="Transform Serasa data",
    params={"serasa_response": "serasa"},
)


def join_func(context, scr_score, serasa_score, **kwargs):
    scores = {"scr_score": scr_score, "serasa_score": serasa_score}
    return scores


join_transform = Transform(
    func=join_func,
    name="join_transform",
    description="Join scores",
    params={"scr_score": "scr_transform", "serasa_score": "serasa_transform"},
)


# Branching node
def branch_condition_1(context, scores, **kwargs):
    if scores["scr_score"] > 600:
        return "approved"
    if scores["serasa_score"] > 800:
        return "analysis"
    return "denied"


branch_1 = Branch(
    func=branch_condition_1,
    name="branch_1",
    description="Branch data",
    params={"scores": "join_transform"},
    outputs=["approved", "analysis", "denied"],
)

approved = Terminate(
    name="approved",
    description="Terminate data branch",
    return_status=Status.APPROVED,
    dependencies={"condition": ("branch_1", "approved")},
)


analysis = Terminate(
    name="analysis",
    description="Terminate data branch",
    return_status=Status.ANALYSIS,
    dependencies={"condition": ("branch_1", "analysis")},
)

denied = Terminate(
    name="denied",
    description="Terminate data branch",
    return_status=Status.DENIED,
    dependencies={"condition": ("branch_1", "denied")},
)

# Policy
# Input <- schema do input
# Output <- o que fazer quando chegar num terminate
#   1. marcar o resultado da run no nosso db
#   2. retornar o status da run em alguma configuração que o usuario deu


# TODO: we may want to specify some data to be used in the output.
# Example: return the tax id, status, duration, limit etc
# User-configurable callback
def return_fn(
    context: OpExecutionContext,
    base_url: str,
    policy_id: int,
    run_id: int,
    status: Status,
) -> bool:
    url = f"{base_url}/"
    dagster_run_id: str = context.run_id
    status: str = status.value
    context.log.info(f"Returned status {status} to {url} for run {dagster_run_id}")
    result = requests.post(
        url, data={"dagster_run_id": dagster_run_id, "status": status}
    )
    if result.status_code not in {200, 204}:
        msg = f"Error {result.status_code} Failed to return status {status} to {url} for run {dagster_run_id}"
        context.log.error(msg)
        return False
    return True


demo_policy = Policy(
    name="policy",
    description="Demo policy created to test Vulkan functionality",
    nodes=[
        scr_body,
        scr,
        serasa_body,
        serasa,
        scr_transform,
        serasa_transform,
        join_transform,
        branch_1,
        approved,
        analysis,
        denied,
    ],
    input_schema={"cpf": str},
    output_callback=partial(return_fn, base_url=CLIENT_SERVER_URL),
)
