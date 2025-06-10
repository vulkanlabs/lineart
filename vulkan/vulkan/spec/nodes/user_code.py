import ast
from inspect import getsource
from textwrap import dedent
from typing import Any, Callable

from jinja2 import Template

from vulkan.spec.dependency import DependencyDict
from vulkan.spec.nodes.metadata import DecisionCondition


def get_source_code(func: Callable) -> str:
    """Get the source code of a function.

    Args:
        func (Callable): The function to get the source code from.

    Returns:
        str: The source code of the function.
    """
    return dedent(getsource(func))


def get_udf_instance(
    user_code: str, dependencies: dict[str, DependencyDict] | None
) -> Callable:
    argnames = None
    if dependencies:
        argnames = list(dependencies.keys())

    try:
        fn_name, udf_code = _validate_user_code(user_code, argnames)
    except UserCodeException as e:
        raise e
    # FIXME: this is BAD and should NEVER see the light of day.
    # It is here for quick validation only.
    exec(udf_code)
    udf_instance = locals()[fn_name]
    return udf_instance


def _validate_user_code(user_code: str, argnames: list[str] | None) -> tuple[str, str]:
    """Validate, parse and compile custom user code.

    WARNING: this function is *obviously* sensitive. It should only ever
    be run in isolated environments, and the user code in question
    should never be executed. Doing otherwise allows arbitrary code to
    execute, and may cause crashes even with "well-intentioned" code.
    """

    if not isinstance(user_code, str):
        raise TypeError(f"Expected user code as string, got ({type(user_code)})")

    node_name = "vulkan_user_code"
    valid = False

    try:
        parsed = ast.parse(
            source=user_code,
            filename=node_name,
            mode="exec",
            type_comments=True,
        )

        if is_valid_function(parsed, node_name):
            udf_code = user_code
            fn_name = get_fn_name(parsed)
            valid = True
    except Exception:
        # If the user code is not a function, we wrap it in a function
        # and try to parse it again.
        pass

    if not valid:
        udf_code = udf(node_name, user_code, argnames)
        fn_name = f"_udf_{node_name}"
        try:
            parsed = ast.parse(
                source=udf_code,
                filename=fn_name,
                mode="exec",
                type_comments=True,
            )
        except ValueError as e:
            raise UserCodeException("Invalid symbol (\0) in user code") from e
        except Exception as e:
            raise UserCodeException("User code is invalid") from e

    try:
        _ = compile(
            udf_code,
            filename=node_name,
            mode="exec",
        )
    except SyntaxError as e:
        raise UserCodeException("User code is invalid") from e

    return fn_name, udf_code


def is_valid_function(tree: ast.Module, node_name: str) -> bool:
    if len(tree.body) != 1:
        return False

    if not isinstance(tree.body[0], ast.FunctionDef):
        return False

    return True


def get_fn_name(tree: ast.Module) -> str:
    assert len(tree.body) == 1
    assert isinstance(tree.body[0], ast.FunctionDef)
    stmt: ast.FunctionDef = tree.body[0]
    return stmt.name


class UserCodeException(Exception):
    def __init__(self, *args):
        super().__init__(*args)


def udf(name: str, source: str, argnames: list[str] | None) -> str:
    return _USER_FN_TEMPLATE.render(
        node_name=name,
        source=source,
        argnames=argnames,
    )


_USER_FN_STRING = """
def _udf_{{node_name}}(*args, **kwargs):
{%- if argnames -%}
    {% for arg in argnames %}
    if "{{arg}}" not in kwargs:
        raise ValueError("Missing required argument '{{arg}}'")
    {{arg}} = kwargs.get("{{arg}}")
    {% endfor -%}
{%- endif -%}

{{ source|indent }}
"""

_USER_FN_TEMPLATE = Template(_USER_FN_STRING)


def get_conditions_udf_instance(
    name: str,
    conditions: list[DecisionCondition],
    context: dict[str, Any] | None = None,
) -> str:
    if context is None:
        context = {}
    udf_code = _USER_FN_FROM_CONDITIONS_TEMPLATE.render(
        node_name=name,
        conditions=conditions,
        context=context,
    )
    print(udf_code)
    exec(udf_code)
    udf_instance = locals()[f"_udf_conditions_{name}"]
    return udf_instance


_USER_FN_FROM_CONDITIONS_STRING = """
def _udf_conditions_{{node_name}}(*args, **kwargs):
    {% for arg, value in context.items() -%}
    {{arg}} = kwargs.get("{{arg}}")
    {% endfor -%}


    {%- for condition in conditions %}
    {%- if condition.decision_type.value == "if" -%}
    if {{ condition.condition }}:
        return "{{ condition.output }}"
    {% elif condition.decision_type.value == "else-if" -%}
    if {{ condition.condition }}:
        return "{{ condition.output }}"
    {% endif -%}
    {% endfor -%}

    {% set else_condition = conditions | selectattr("decision_type.value", "equalto", "else") | first %}
    return "{{ else_condition.output }}"
"""

_USER_FN_FROM_CONDITIONS_TEMPLATE = Template(_USER_FN_FROM_CONDITIONS_STRING)
