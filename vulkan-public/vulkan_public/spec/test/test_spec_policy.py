import pytest

from vulkan_public.spec.dependency import Dependency
from vulkan_public.spec.policy import PolicyDefinitionNode


def branch_condition_1(context, scores, **kwargs):
    context.log.info(f"BranchNode data: {scores}")
    if scores["score"] > context.env.get("SCORE_CUTOFF", 500):
        return "approved"
    return "denied"


TEST_TABLE = {
    "Policy Definition Node - Valid function as String": (
        PolicyDefinitionNode,
        {
            "name": "subpolicy",
            "node_type": "POLICY",
            "description": None,
            "dependencies": {
                "input_data": Dependency(
                    node="input_node", output=None, key=None, hierarchy=None
                )
            },
            "metadata": {
                "policy_definition": {
                    "nodes": [
                        {
                            "name": "branch_1",
                            "node_type": "BRANCH",
                            "description": "BranchNode data",
                            "dependencies": {
                                "scores": Dependency(
                                    node="input_node",
                                    output=None,
                                    key=None,
                                    hierarchy=None,
                                )
                            },
                            "metadata": {
                                "choices": ["approved", "denied"],
                                "function_code": 'def branch_condition_1(context, scores, **kwargs):\n    context.log.info(f"BranchNode data: {scores}")\n    if scores["score"] > context.env.get("SCORE_CUTOFF", 500):\n        return "approved"\n    return "denied"\n',
                                "func": None,
                                "source_code": 'def branch_condition_1(context, scores, **kwargs):\n    context.log.info(f"BranchNode data: {scores}")\n    if scores["score"] > context.env.get("SCORE_CUTOFF", 500):\n        return "approved"\n    return "denied"\n',
                            },
                        },
                        {
                            "name": "approved",
                            "node_type": "TERMINATE",
                            "description": "TerminateNode data branch",
                            "dependencies": {
                                "condition": Dependency(
                                    node="branch_1",
                                    output="approved",
                                    key=None,
                                    hierarchy=None,
                                )
                            },
                            "metadata": {"return_status": "APPROVED"},
                        },
                        {
                            "name": "denied",
                            "node_type": "TERMINATE",
                            "description": "TerminateNode data branch",
                            "dependencies": {
                                "condition": Dependency(
                                    node="branch_1",
                                    output="denied",
                                    key=None,
                                    hierarchy=None,
                                )
                            },
                            "metadata": {"return_status": "DENIED"},
                        },
                    ],
                    "input_schema": {"tax_id": "str", "score": "int"},
                    "output_callback": None,
                    "config_variables": ["SCORE_CUTOFF"],
                }
            },
        },
    ),
    "Policy Definition Node - Chunk as String": (
        PolicyDefinitionNode,
        {
            "name": "subpolicy",
            "node_type": "POLICY",
            "description": None,
            "dependencies": {
                "input_data": Dependency(
                    node="input_node", output=None, key=None, hierarchy=None
                )
            },
            "metadata": {
                "policy_definition": {
                    "nodes": [
                        {
                            "name": "branch_1",
                            "node_type": "BRANCH",
                            "description": "BranchNode data",
                            "dependencies": {
                                "scores": Dependency(
                                    node="input_node",
                                    output=None,
                                    key=None,
                                    hierarchy=None,
                                )
                            },
                            "metadata": {
                                "choices": ["approved", "denied"],
                                "function_code": '\nreturn "approved"\n',
                                "func": None,
                                "source_code": '\nreturn "approved"\n',
                            },
                        },
                        {
                            "name": "approved",
                            "node_type": "TERMINATE",
                            "description": "TerminateNode data branch",
                            "dependencies": {
                                "condition": Dependency(
                                    node="branch_1",
                                    output="approved",
                                    key=None,
                                    hierarchy=None,
                                )
                            },
                            "metadata": {"return_status": "APPROVED"},
                        },
                        {
                            "name": "denied",
                            "node_type": "TERMINATE",
                            "description": "TerminateNode data branch",
                            "dependencies": {
                                "condition": Dependency(
                                    node="branch_1",
                                    output="denied",
                                    key=None,
                                    hierarchy=None,
                                )
                            },
                            "metadata": {"return_status": "DENIED"},
                        },
                    ],
                    "input_schema": {"tax_id": "str", "score": "int"},
                    "output_callback": None,
                    "config_variables": ["SCORE_CUTOFF"],
                }
            },
        },
    ),
    "Policy Definition Node - Code": (
        PolicyDefinitionNode,
        {
            "name": "subpolicy",
            "node_type": "POLICY",
            "description": None,
            "dependencies": {
                "input_data": Dependency(
                    node="input_node", output=None, key=None, hierarchy=None
                )
            },
            "metadata": {
                "policy_definition": {
                    "nodes": [
                        {
                            "name": "branch_1",
                            "node_type": "BRANCH",
                            "description": "BranchNode data",
                            "dependencies": {
                                "scores": Dependency(
                                    node="input_node",
                                    output=None,
                                    key=None,
                                    hierarchy=None,
                                )
                            },
                            "metadata": {
                                "choices": ["approved", "denied"],
                                "function_code": 'def branch_condition_1(context, scores, **kwargs):\n    context.log.info(f"BranchNode data: {scores}")\n    if scores["score"] > context.env.get("SCORE_CUTOFF", 500):\n        return "approved"\n    return "denied"\n',
                                "func": branch_condition_1,
                                "source_code": None,
                            },
                        },
                        {
                            "name": "approved",
                            "node_type": "TERMINATE",
                            "description": "TerminateNode data branch",
                            "dependencies": {
                                "condition": Dependency(
                                    node="branch_1",
                                    output="approved",
                                    key=None,
                                    hierarchy=None,
                                )
                            },
                            "metadata": {"return_status": "APPROVED"},
                        },
                        {
                            "name": "denied",
                            "node_type": "TERMINATE",
                            "description": "TerminateNode data branch",
                            "dependencies": {
                                "condition": Dependency(
                                    node="branch_1",
                                    output="denied",
                                    key=None,
                                    hierarchy=None,
                                )
                            },
                            "metadata": {"return_status": "DENIED"},
                        },
                    ],
                    "input_schema": {"tax_id": "str", "score": "int"},
                    "output_callback": None,
                    "config_variables": ["SCORE_CUTOFF"],
                }
            },
        },
    ),
}


@pytest.mark.parametrize(
    ["node_cls", "spec"],
    [(cls, spec) for cls, spec in TEST_TABLE.values()],
    ids=list(TEST_TABLE.keys()),
)
def test_node_from_spec(node_cls, spec):
    node = node_cls.from_dict(spec)
    assert node.name == spec["name"]
    assert node.type.value == spec["node_type"]
    assert node.description == spec.get("description", None)
    round_trip = node_cls.from_dict(node.to_dict())
    assert round_trip == node
