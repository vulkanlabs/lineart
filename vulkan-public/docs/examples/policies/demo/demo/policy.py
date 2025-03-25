from enum import Enum
from functools import partial

import requests

from vulkan_public.spec.component import ComponentInstance, ComponentInstanceConfig
from vulkan_public.spec.dependency import INPUT_NODE, Dependency
from vulkan_public.spec.nodes.base import BranchNode, HTTPConnectionNode, TerminateNode
from vulkan_public.spec.policy import PolicyDefinition

DATA_SERVER_URL = "http://testdata:5000"
CLIENT_SERVER_URL = "http://echo:80/post"

http_params = dict(method="GET", headers={}, params={})


class Status(Enum):
    APPROVED = "APPROVED"
    ANALYSIS = "ANALYSIS"
    DENIED = "DENIED"


scr_data = HTTPConnectionNode(
    name="scr_data",
    description="Consulta dados do SCR para o CPF informado",
    dependencies={"body": Dependency(INPUT_NODE)},
    url="http://api.scr.com.br/",
    method="GET",
    headers={},
    params={},
)


def has_scr_data(context, scr_data, **kwargs):
    context.log.info(f"Dados recebidos do SCR: {scr_data}")

    if scr_data["num_ifs"] > 0:
        return "OK"
    else:
        return "MISSING_DATA"


check_scr_ok = BranchNode(
    name="check_scr_ok",
    description="Checa se os dados do SCR foram retornados",
    dependencies={"scr_data": Dependency("scr_data")},
    func=has_scr_data,
    choices=["OK", "MISSING_DATA"],
)

negado_sem_scr = TerminateNode(
    name="Negado_Sem_SCR",
    description="Negado por falta de dados no SCR",
    return_status=Status.DENIED,
    dependencies={"condition": Dependency("check_scr_ok", "MISSING_DATA")},
)

scr_model = ComponentInstance(
    name="scr_component",
    version="v0.0.1",
    config=ComponentInstanceConfig(
        name="scr_model",
        description="Get SCR score",
        dependencies={
            "cpf": Dependency(INPUT_NODE, key="cpf"),
            "condition": Dependency("check_scr_ok", "OK"),
        },
        # Caminho do modelo criado pelo time de ML
        instance_params={
            "server_url": "https://model-example.run.app",
        },
    ),
)


def decision_scr_score(context, scr_score, **kwargs):
    if scr_score > 600:
        return "approved"
    else:
        return "denied"


decisao = BranchNode(
    name="decisao_final",
    description="Decide se o cliente é aprovado ou não",
    dependencies={"scr_score": Dependency(scr_model.config.name)},
    func=decision_scr_score,
    choices=["approved", "denied"],
)

approved = TerminateNode(
    name="Aprovado",
    description="Terminate data branch",
    return_status=Status.APPROVED,
    dependencies={"condition": Dependency("decisao_final", "approved")},
)


denied = TerminateNode(
    name="Negado",
    description="Terminate data branch",
    return_status=Status.DENIED,
    dependencies={"condition": Dependency("decisao_final", "denied")},
)


def return_fn(
    context,
    url: str,
    run_id: int,
    status: str,
    **kwargs,
) -> bool:
    dagster_run_id: str = context.run_id
    result = requests.post(
        url,
        data={
            "dagster_run_id": dagster_run_id,
            "run_id": run_id,
            "status": status,
        },
    )
    if result.status_code not in {200, 204}:
        msg = f"Error {result.status_code} Failed to return status {status} to {url} for run {dagster_run_id}"
        context.log.error(msg)
        return False
    return True


demo_policy = PolicyDefinition(
    nodes=[
        scr_data,
        check_scr_ok,
        negado_sem_scr,
        decisao,
        approved,
        denied,
    ],
    components=[scr_model],
    input_schema={"cpf": str},
    output_callback=partial(return_fn, url=CLIENT_SERVER_URL),
)
