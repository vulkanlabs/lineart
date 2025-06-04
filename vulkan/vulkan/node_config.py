from jinja2 import Environment, Template
from pydantic import BaseModel

BaseType = str | int | float | bool


class EnvVarConfig(BaseModel):
    env: str


class RunTimeParam(BaseModel):
    param: str


ParameterType = BaseType | list[BaseType] | EnvVarConfig | RunTimeParam
ConfigurableDict = dict[str, ParameterType]


def _visit_nodes(node, visitor_func):
    """Helper function to recursively visit all nodes in a Jinja2 AST."""
    visitor_func(node)
    for child in getattr(node, "iter_child_nodes", lambda: [])():
        _visit_nodes(child, visitor_func)


def _create_env_var_visitor(vars_list: list):
    """Creates a visitor function to extract environment variables."""

    def visitor(node):
        if hasattr(node, "node") and hasattr(node, "attr"):
            if hasattr(node.node, "name") and node.node.name == "env":
                vars_list.append(node.attr)

    return visitor


def _create_runtime_param_visitor(vars_list: list):
    """Creates a visitor function to extract runtime parameters."""

    def visitor(node):
        if hasattr(node, "name") and not hasattr(node, "attr"):
            if node.name != "env":
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
    """
    if spec is None:
        spec = {}

    for key, value in spec.items():
        if isinstance(value, RunTimeParam) or isinstance(value, EnvVarConfig):
            value = normalize_to_template(value)
        if isinstance(value, str):
            spec[key] = resolve_template(value, local_variables, env_variables)

    return spec


def resolve_template(value: str, local_variables: dict, env_variables: dict) -> str:
    """
    Resolve a Jinja2 template string using provided local and environment variables.
    This function uses Jinja2 to render the template with the given context.
    """
    if not isinstance(value, str):
        raise ValueError(
            f"Expected a string for template resolution, got {type(value)}"
        )

    if not value.strip():
        return value

    template = Template(value)
    context = {"env": env_variables, **local_variables}
    return template.render(context)


def normalize_to_template(value: ParameterType) -> str:
    """
    Normalize both object-based and template-based configurations to template format.

    Examples:
    - {"param": "variable"} -> "{{variable}}"
    - {"env": "variable"} -> "{{env.variable}}"
    - "{{variable}}" -> "{{variable}}" (unchanged)
    """
    if isinstance(value, RunTimeParam):
        return f"{{{{{value.param}}}}}"
    elif isinstance(value, EnvVarConfig):
        return f"{{{{env.{value.env}}}}}"
    elif isinstance(value, (str, int, float, bool)):
        return str(value)
    elif isinstance(value, list):
        # For lists, normalize each element
        return [normalize_to_template(item) for item in value]
    else:
        return str(value)


def normalize_mapping(spec: ConfigurableDict) -> dict[str, str]:
    """
    Normalize a ConfigurableDict to template format.

    Returns a dictionary where all values are normalized to template strings.
    """
    if spec is None:
        return {}

    return {key: normalize_to_template(value) for key, value in spec.items()}
