import ast
import re
from typing import Any, Literal

from jinja2 import Environment, Template, nodes
from pydantic import BaseModel, TypeAdapter, ValidationError

_BaseType = str | int | float | bool
_ListType = list[_BaseType]
_ShallowDictType = dict[str, _BaseType | _ListType]
_ValueType = _BaseType | _ListType | _ShallowDictType
_DictType = dict[str, _ValueType]


class EnvVarConfig(BaseModel):
    env: str


class RunTimeParam(BaseModel):
    param: str
    value_type: Literal["str", "int", "float", "auto"] = "auto"


_ParameterType = _BaseType | _ListType | _DictType | EnvVarConfig | RunTimeParam
ConfigurableDict = dict[str, _ParameterType]
configurable_dict_adapter = TypeAdapter(ConfigurableDict)


def _visit_nodes(node, visitor_func):
    """Helper function to recursively visit all nodes in a Jinja2 AST."""
    visitor_func(node)
    for child in getattr(node, "iter_child_nodes", lambda: [])():
        _visit_nodes(child, visitor_func)


def _create_env_var_visitor(vars_list: list):
    """Creates a visitor function to extract environment variables.

    Extracts environment variable names from Jinja2 templates (e.g., {{env.VAR}}).
    Only matches attribute access on the 'env' object (Getattr nodes).
    """

    def visitor(node):
        # Only extract Getattr nodes where the base object is the 'env' Name node
        # This matches patterns like {{env.MY_VAR}}
        if isinstance(node, nodes.Getattr):
            if isinstance(node.node, nodes.Name) and node.node.name == "env":
                vars_list.append(node.attr)

    return visitor


def _create_runtime_param_visitor(vars_list: list):
    """Creates a visitor function to extract runtime parameters.

    Extracts simple variable names from Jinja2 templates (e.g., {{variable}}).
    Excludes environment variables ({{env.VAR}}) and the 'env' object itself.

    This visitor handles RunTimeParam instances which may have different value_type
    specifications (str, int, float, auto), but at the template level we only
    extract the variable names - type information is preserved in the RunTimeParam
    object itself, not in the template string.
    """

    def visitor(node):
        if isinstance(node, nodes.Name) and node.name != "env":
            vars_list.append(node.name)

    return visitor


def _extract_variables_from_template_string(
    template_string: str, visitor_factory
) -> list[str]:
    """
    Helper to extract variables from a Jinja2 template string using a provided visitor factory.
    """
    if not template_string or not isinstance(template_string, str):
        return []

    extracted_vars = []
    env = Environment()

    ast = env.parse(template_string)
    visitor_func = visitor_factory(extracted_vars)
    _visit_nodes(ast, visitor_func)

    return extracted_vars


def extract_env_vars(spec: ConfigurableDict) -> list[str]:
    """
    Extract environment variable names from a ConfigurableDict using Jinja2 AST parsing.

    Returns a list of environment variable names found in the spec.
    Raises TemplateSyntaxError for invalid Jinja2 syntax.
    """
    if spec is None:
        return []

    env_vars = []

    for key, value in spec.items():
        # Try to convert dict to RunTimeParam or EnvVarConfig if applicable
        value = _try_cast_to_config_object(value)

        if isinstance(value, EnvVarConfig):
            env_vars.append(value.env)
        elif isinstance(value, str):
            try:
                env_vars.extend(
                    _extract_variables_from_template_string(
                        value, _create_env_var_visitor
                    )
                )
            except Exception as e:
                raise ValueError(
                    f"Invalid Jinja2 template in field '{key}': {value}"
                ) from e

    return list(set(env_vars))


def extract_runtime_params(spec: ConfigurableDict) -> list[str]:
    """
    Extract runtime parameter names from a ConfigurableDict using Jinja2 AST parsing.

    Returns a list of runtime parameter names found in the spec.
    Raises TemplateSyntaxError for invalid Jinja2 syntax.
    """
    if spec is None:
        return []

    runtime_params = []

    for key, value in spec.items():
        # Try to convert dict to RunTimeParam or EnvVarConfig if applicable
        value = _try_cast_to_config_object(value)

        if isinstance(value, RunTimeParam):
            runtime_params.append(value.param)
        elif isinstance(value, str):
            try:
                runtime_params.extend(
                    _extract_variables_from_template_string(
                        value, _create_runtime_param_visitor
                    )
                )
            except Exception as e:
                raise ValueError(
                    f"Invalid Jinja2 template in field '{key}': {value}"
                ) from e

    return list(set(runtime_params))


def extract_env_vars_from_string(template: str) -> list[str]:
    """
    Extract environment variable names from a template using Jinja2 AST parsing.

    Returns a list of environment variable names found in the template.
    Raises ValueError for invalid Jinja2 syntax.
    """
    if not template or not isinstance(template, str):
        return []

    try:
        return list(
            set(
                _extract_variables_from_template_string(
                    template, _create_env_var_visitor
                )
            )
        )
    except Exception as e:
        raise ValueError(f"Invalid Jinja2 template: {template}") from e


def extract_runtime_params_from_string(template: str) -> list[str]:
    """
    Extract runtime parameter names from a template using Jinja2 AST parsing.

    Returns a list of runtime parameter names found in the template.
    Raises ValueError for invalid Jinja2 syntax.
    """
    if not template or not isinstance(template, str):
        return []

    try:
        return list(
            set(
                _extract_variables_from_template_string(
                    template, _create_runtime_param_visitor
                )
            )
        )
    except Exception as e:
        raise ValueError(f"Invalid Jinja2 template: {template}") from e


def configure_fields(
    spec: ConfigurableDict, local_variables: dict, env_variables: dict
) -> dict:
    """
    Configure fields in a specification dictionary by resolving templates.

    This function replaces any RunTimeParam or EnvVarConfig instances with their
    corresponding template strings, and resolves any string templates using
    the provided node and environment variables.

    Dictionary casting:
    - Dicts with "param" key are automatically converted to RunTimeParam
    - Dicts with "env" key are automatically converted to EnvVarConfig
    - This enables seamless handling of both object and serialized representations

    Type handling:
    - RunTimeParam: Uses the value_type field to determine expected type
    - EnvVarConfig: Always returns strings (matching OS environment variable semantics)
    - Plain templates: Uses "auto" type inference
    """
    if spec is None:
        spec = {}

    for key, value in spec.items():
        expected_type = "auto"

        # Try to convert dict to RunTimeParam or EnvVarConfig if applicable
        value = _try_cast_to_config_object(value)

        if isinstance(value, RunTimeParam):
            expected_type = value.value_type
            value = normalize_to_template(value)
        elif isinstance(value, EnvVarConfig):
            # Environment variables are always strings (OS semantics)
            expected_type = "str"
            value = normalize_to_template(value)

        if _is_template_like(value):
            spec[key] = resolve_template(
                value, local_variables, env_variables, expected_type
            )

    return spec


def _try_cast_to_config_object(value: Any) -> RunTimeParam | EnvVarConfig | Any:
    """
    Try to convert a dict to RunTimeParam or EnvVarConfig if applicable.

    Args:
        value: The value to potentially convert

    Returns:
        RunTimeParam if dict has "param" key and is valid
        EnvVarConfig if dict has "env" key and is valid
        Original value otherwise
    """
    if not isinstance(value, dict):
        return value

    # Try to convert to RunTimeParam
    if "param" in value:
        try:
            return RunTimeParam(**value)
        except ValidationError:
            pass

    # Try to convert to EnvVarConfig
    if "env" in value:
        try:
            return EnvVarConfig(**value)
        except ValidationError:
            pass

    return value


def _is_template_like(value: Any) -> bool:
    if not isinstance(value, str):
        return False

    # Check if the string contains at least one Jinja2 template expression
    return bool(re.search(r"\{\{.*?\}\}", value))


def _convert_to_type(value: str, target_type: str) -> int | float | bool:
    """
    Convert a string value to the specified type with clear error messages.

    Args:
        value: The string value to convert
        target_type: One of "int", "float"

    Returns:
        The converted value

    Raises:
        ValueError: If the conversion fails
    """
    if target_type not in ("int", "float"):
        raise ValueError(f"Unsupported target type for conversion: {target_type}")

    try:
        if target_type == "int":
            return int(value)
        elif target_type == "float":
            return float(value)
    except (ValueError, TypeError, AttributeError) as e:
        raise ValueError(
            f"Cannot convert template result '{value}' to {target_type}: {e}"
        )


def resolve_template(
    value: str,
    local_variables: dict,
    env_variables: dict,
    expected_type: str = "auto",
) -> _ValueType:
    """
    Resolve a Jinja2 template string using provided local and environment variables.

    Args:
        value: The template string to resolve (e.g., "{{variable}}")
        local_variables: Dictionary of runtime variables
        env_variables: Dictionary of environment variables
        expected_type: Expected type of the result. One of:
            - "str": Always return a string (no type conversion)
            - "int": Convert to integer
            - "float": Convert to float
            - "auto": Attempt to infer type using ast.literal_eval (default)

    Returns:
        The resolved value with the appropriate type

    Raises:
        ValueError: If template is invalid or type conversion fails
    """
    if not isinstance(value, str):
        raise ValueError(
            f"Expected a string for template resolution, got {type(value)}"
        )

    if not value.strip():
        return value

    template = Template(value)
    context = {"env": env_variables, **local_variables}
    rendered = template.render(context)

    # Explicit string type - no conversion needed
    if expected_type == "str":
        return rendered

    # Explicit typed conversion
    if expected_type in ("int", "float"):
        return _convert_to_type(rendered, expected_type)

    # Auto - infer type using ast.literal_eval
    # This attempts to evaluate the rendered template as a Python literal.
    # If it looks like a bool, list, dict, etc, it will be converted.
    try:
        return ast.literal_eval(rendered)
    except (ValueError, SyntaxError):
        return rendered


def resolve_value(
    value: Any,
    jinja_context: dict[str, Any],
    env_variables: dict[str, Any],
) -> Any:
    """
    Recursively resolve values that may contain templates.

    Handles strings (templates), dictionaries, and lists by recursively
    resolving any template expressions found within them.

    Args:
        value: The value to resolve (str, dict, list, or other)
        jinja_context: Dictionary of local/runtime variables
        env_variables: Dictionary of environment variables

    Returns:
        The resolved value with templates replaced

    Examples:
        >>> resolve_value("{{x}}", {"x": 5}, {})
        5
        >>> resolve_value({"a": "{{x}}"}, {"x": 5}, {})
        {"a": 5}
        >>> resolve_value(["{{x}}", "{{y}}"], {"x": 5, "y": 10}, {})
        [5, 10]
    """
    if isinstance(value, str):
        try:
            # Use Jinja2-based template resolution with environment variables
            return resolve_template(value, jinja_context, env_variables)
        except Exception:
            # If template resolution fails, return original value
            return value
    elif isinstance(value, dict):
        return {
            k: resolve_value(v, jinja_context, env_variables) for k, v in value.items()
        }
    elif isinstance(value, list):
        return [resolve_value(item, jinja_context, env_variables) for item in value]
    else:
        return value


def normalize_to_template(value: _ParameterType) -> str:
    """
    Normalize both object-based and template-based configurations to template format.

    Examples:
    - {"param": "variable"} -> "{{variable}}"
    - {"env": "variable"} -> "{{env.variable}}"
    - "{{variable}}" -> "{{variable}}" (unchanged)
    - "variable" -> "{{variable}}"
    """
    if isinstance(value, RunTimeParam):
        return f"{{{{{value.param}}}}}"
    elif isinstance(value, EnvVarConfig):
        return f"{{{{env.{value.env}}}}}"
    elif isinstance(value, list):
        # For lists, normalize each element
        return [normalize_to_template(item) for item in value]
    elif isinstance(value, str) and value.startswith("{{") and value.endswith("}}"):
        return value
    else:
        return f"{{{{{value}}}}}"


def normalize_mapping(spec: ConfigurableDict) -> dict[str, str]:
    """
    Normalize a ConfigurableDict to template format.

    Returns a dictionary where all values are normalized to template strings.
    """
    if spec is None:
        return {}

    return {key: normalize_to_template(value) for key, value in spec.items()}
