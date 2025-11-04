"""
Test cases demonstrating the numeric string conversion issue in resolve_template.

The issue: ast.literal_eval() converts numeric strings to their Python types,
which causes problems when the template should resolve to a string but the
value happens to look like a number.

Examples:
- Tax IDs like "12345678901" become integers, breaking APIs that expect strings
- Phone numbers like "5551234567" become integers, losing leading zeros
- ZIP codes like "01234" become integers, losing leading zeros
- Account numbers that look numeric but must remain strings
"""

import pytest
from vulkan.node_config import (
    EnvVarConfig,
    RunTimeParam,
    _is_template_like,
    configure_fields,
    extract_env_vars,
    extract_env_vars_from_string,
    extract_runtime_params,
    extract_runtime_params_from_string,
    resolve_template,
)


class TestResolveTemplateNumericStringIssue:
    """Test cases demonstrating the numeric string conversion bug."""

    def test_tax_id_converted_to_int(self):
        """
        Tax IDs are often numeric but MUST remain strings.
        Many APIs validate them as strings with specific formats.

        Example: Brazilian CPF "12345678901" should stay as string,
        not be converted to int 12345678901.
        """
        template = "{{tax_id}}"
        local_vars = {"tax_id": "12345678901"}
        env_vars = {}

        result = resolve_template(template, local_vars, env_vars, "str")

        assert isinstance(result, str), f"Expected str, got {type(result)}"
        assert result == "12345678901"

    def test_phone_number_with_leading_zeros(self):
        """
        Phone numbers with leading zeros lose them when converted to int.

        Example: "0123456789" becomes 123456789 (int), losing the leading zero.
        """
        template = "{{phone}}"
        local_vars = {"phone": "0123456789"}
        env_vars = {}

        result = resolve_template(template, local_vars, env_vars, "str")

        assert isinstance(result, str), f"Expected str, got {type(result)}"
        assert result == "0123456789"
        assert result.startswith("0"), "Leading zero was lost"

    def test_zip_code_with_leading_zeros(self):
        """
        US ZIP codes can start with zeros and must remain strings.

        Example: "01234" (Boston area) becomes 1234 (int).
        """
        template = "{{zip_code}}"
        local_vars = {"zip_code": "01234"}
        env_vars = {}

        result = resolve_template(template, local_vars, env_vars, "str")

        assert isinstance(result, str), f"Expected str, got {type(result)}"
        assert result == "01234"
        assert len(result) == 5, f"ZIP code should be 5 digits, got {len(result)}"

    def test_account_number_as_string(self):
        """
        Account numbers may be purely numeric but must remain strings.

        Example: "9876543210" should not become int.
        """
        template = "{{account_number}}"
        local_vars = {"account_number": "9876543210"}
        env_vars = {}

        result = resolve_template(template, local_vars, env_vars, "str")

        assert isinstance(result, str), f"Expected str, got {type(result)}"
        assert result == "9876543210"

    def test_env_var_numeric_string(self):
        """
        Environment variables are always strings in the OS.
        Even if they look numeric, they should remain strings.

        Example: API_KEY="11223344556677889900" should stay as string.
        """
        template = "{{env.API_KEY}}"
        local_vars = {}
        env_vars = {"API_KEY": "11223344556677889900"}

        result = resolve_template(template, local_vars, env_vars, "str")

        assert isinstance(result, str), f"Expected str, got {type(result)}"
        assert result == "11223344556677889900"

    def test_padded_id_with_zeros(self):
        """
        IDs that are zero-padded for formatting must preserve padding.

        Example: "00042" should not become 42.
        """
        template = "{{order_id}}"
        local_vars = {"order_id": "00042"}
        env_vars = {}

        result = resolve_template(template, local_vars, env_vars, "str")

        assert isinstance(result, str), f"Expected str, got {type(result)}"
        assert result == "00042"
        assert len(result) == 5, f"Expected length 5, got {len(result)}"


class TestResolveTemplateEdgeCases:
    """Additional edge cases related to the numeric string issue."""

    def test_float_as_string(self):
        """Float-like strings should not be converted to float."""
        template = "{{version}}"
        local_vars = {"version": "1.0"}
        env_vars = {}

        result = resolve_template(template, local_vars, env_vars, "str")

        assert isinstance(result, str), f"Expected str, got {type(result)}"
        assert result == "1.0"

    def test_scientific_notation_string(self):
        """Strings that look like scientific notation should stay strings."""
        template = "{{code}}"
        local_vars = {"code": "1e10"}
        env_vars = {}

        result = resolve_template(template, local_vars, env_vars, "str")

        assert isinstance(result, str), f"Expected str, got {type(result)}"
        assert result == "1e10"

    def test_hex_string(self):
        """Hex-like strings should stay strings."""
        template = "{{color}}"
        local_vars = {"color": "0xFF00FF"}
        env_vars = {}

        result = resolve_template(template, local_vars, env_vars, "str")

        assert isinstance(result, str), f"Expected str, got {type(result)}"
        assert result == "0xFF00FF"

    def test_negative_number_string(self):
        """Negative number strings should not be converted."""
        template = "{{adjustment}}"
        local_vars = {"adjustment": "-100"}
        env_vars = {}

        result = resolve_template(template, local_vars, env_vars, "str")

        assert isinstance(result, str), f"Expected str, got {type(result)}"
        assert result == "-100"


class TestResolveTemplateSuccessCases:
    """Test cases showing the FIX using explicit type hints."""

    def test_env_var_config_always_returns_string(self):
        """EnvVarConfig in configure_fields always returns strings."""
        spec = {"api_key": EnvVarConfig(env="API_KEY")}
        local_vars = {}
        env_vars = {"API_KEY": "11223344556677889900"}

        result = configure_fields(spec, local_vars, env_vars)

        assert isinstance(result["api_key"], str)
        assert result["api_key"] == "11223344556677889900"

    def test_runtime_param_with_string_type(self):
        """RunTimeParam with value_type='str' preserves strings."""
        spec = {"tax_id": RunTimeParam(param="user_tax_id", value_type="str")}
        local_vars = {"user_tax_id": "12345678901"}
        env_vars = {}

        result = configure_fields(spec, local_vars, env_vars)

        assert isinstance(result["tax_id"], str)
        assert result["tax_id"] == "12345678901"

    def test_runtime_param_with_int_type(self):
        """RunTimeParam with value_type='int' converts to int."""
        spec = {"count": RunTimeParam(param="num_items", value_type="int")}
        local_vars = {"num_items": "42"}
        env_vars = {}

        result = configure_fields(spec, local_vars, env_vars)

        assert isinstance(result["count"], int)
        assert result["count"] == 42

    def test_runtime_param_with_float_type(self):
        """RunTimeParam with value_type='float' converts to float."""
        spec = {"price": RunTimeParam(param="amount", value_type="float")}
        local_vars = {"amount": "19.99"}
        env_vars = {}

        result = configure_fields(spec, local_vars, env_vars)

        assert isinstance(result["price"], float)
        assert result["price"] == 19.99

    def test_runtime_param_with_auto_infers_bool(self):
        """RunTimeParam with value_type='auto' can infer bool."""
        spec = {"is_active": RunTimeParam(param="active_flag")}  # auto is default
        local_vars = {"active_flag": True}  # Pass actual bool, not string
        env_vars = {}

        result = configure_fields(spec, local_vars, env_vars)

        assert isinstance(result["is_active"], bool)
        assert result["is_active"] is True

    def test_runtime_param_with_auto_type_default(self):
        """RunTimeParam with default value_type='auto' uses inference."""
        spec = {"value": RunTimeParam(param="data")}  # value_type defaults to "auto"
        local_vars = {"data": "42"}
        env_vars = {}

        result = configure_fields(spec, local_vars, env_vars)

        # Auto inference converts "42" to int
        assert isinstance(result["value"], int)
        assert result["value"] == 42

    def test_multiple_fields_with_different_types(self):
        """Mix of different type specifications works correctly."""
        spec = {
            "tax_id": RunTimeParam(param="user_tax_id", value_type="str"),
            "count": RunTimeParam(param="num_items", value_type="int"),
            "price": RunTimeParam(param="amount", value_type="float"),
            "is_active": RunTimeParam(
                param="active_flag"
            ),  # auto type - will infer from value
            "api_key": EnvVarConfig(env="API_KEY"),
        }
        local_vars = {
            "user_tax_id": "12345678901",
            "num_items": "42",
            "amount": "19.99",
            "active_flag": True,  # Pass actual bool
        }
        env_vars = {"API_KEY": "9988776655"}

        result = configure_fields(spec, local_vars, env_vars)

        assert isinstance(result["tax_id"], str)
        assert result["tax_id"] == "12345678901"

        assert isinstance(result["count"], int)
        assert result["count"] == 42

        assert isinstance(result["price"], float)
        assert result["price"] == 19.99

        assert isinstance(result["is_active"], bool)
        assert result["is_active"] is True

        assert isinstance(result["api_key"], str)
        assert result["api_key"] == "9988776655"

    def test_actual_integer_value(self):
        """When the template variable is actually an int, it should return int."""
        template = "{{count}}"
        local_vars = {"count": 42}
        env_vars = {}

        result = resolve_template(template, local_vars, env_vars)

        assert isinstance(result, int)
        assert result == 42

    def test_actual_float_value(self):
        """When the template variable is actually a float, it should return float."""
        template = "{{price}}"
        local_vars = {"price": 19.99}
        env_vars = {}

        result = resolve_template(template, local_vars, env_vars)

        assert isinstance(result, float)
        assert result == 19.99

    def test_actual_boolean_value(self):
        """When the template variable is actually a bool, it should return bool."""
        template = "{{is_active}}"
        local_vars = {"is_active": True}
        env_vars = {}

        result = resolve_template(template, local_vars, env_vars)

        assert isinstance(result, bool)
        assert result is True

    def test_non_numeric_string(self):
        """Non-numeric strings work correctly."""
        template = "{{name}}"
        local_vars = {"name": "John Doe"}
        env_vars = {}

        result = resolve_template(template, local_vars, env_vars)

        # This works correctly
        assert isinstance(result, str)
        assert result == "John Doe"

    def test_alphanumeric_string(self):
        """Alphanumeric strings that can't be parsed as literals work correctly."""
        template = "{{product_code}}"
        local_vars = {"product_code": "ABC123XYZ"}
        env_vars = {}

        result = resolve_template(template, local_vars, env_vars)

        # This works correctly
        assert isinstance(result, str)
        assert result == "ABC123XYZ"

    def test_string_with_special_chars(self):
        """Strings with special characters work correctly."""
        template = "{{email}}"
        local_vars = {"email": "user@example.com"}
        env_vars = {}

        result = resolve_template(template, local_vars, env_vars)

        # This works correctly
        assert isinstance(result, str)
        assert result == "user@example.com"


class TestResolveTemplateTypeConversionErrors:
    """Test error handling for invalid type conversions."""

    def test_invalid_int_conversion(self):
        """Invalid int conversion raises clear error."""
        template = "{{value}}"
        local_vars = {"value": "not_a_number"}
        env_vars = {}

        with pytest.raises(ValueError, match="Cannot convert"):
            resolve_template(template, local_vars, env_vars, expected_type="int")

    def test_invalid_float_conversion(self):
        """Invalid float conversion raises clear error."""
        template = "{{value}}"
        local_vars = {"value": "not_a_float"}
        env_vars = {}

        with pytest.raises(ValueError, match="Cannot convert"):
            resolve_template(template, local_vars, env_vars, expected_type="float")


class TestExtractEnvVarsFromString:
    """Test extracting environment variables from template strings."""

    def test_simple_env_var(self):
        """Extract a single environment variable."""
        template = "{{env.MY_VAR}}"
        result = extract_env_vars_from_string(template)
        assert result == ["MY_VAR"]

    def test_multiple_env_vars(self):
        """Extract multiple environment variables."""
        template = "{{env.VAR1}}_{{env.VAR2}}"
        result = extract_env_vars_from_string(template)
        assert set(result) == {"VAR1", "VAR2"}

    def test_env_var_in_text(self):
        """Extract env var from template with surrounding text."""
        template = "prefix_{{env.API_KEY}}_suffix"
        result = extract_env_vars_from_string(template)
        assert result == ["API_KEY"]

    def test_mixed_env_and_runtime_params(self):
        """Extract only env vars when mixed with runtime params."""
        template = "{{env.API_KEY}}/{{endpoint}}/{{env.REGION}}"
        result = extract_env_vars_from_string(template)
        assert set(result) == {"API_KEY", "REGION"}

    def test_duplicate_env_vars(self):
        """Duplicate env vars should be deduplicated."""
        template = "{{env.VAR}}_{{env.VAR}}"
        result = extract_env_vars_from_string(template)
        assert result == ["VAR"]

    def test_no_template(self):
        """Handle plain string without templates."""
        result = extract_env_vars_from_string("env var text")
        assert result == []

    def test_no_env_vars(self):
        """Return empty list when no env vars present."""
        template = "{{runtime_param}}"
        result = extract_env_vars_from_string(template)
        assert result == []

    def test_empty_string(self):
        """Handle empty string."""
        result = extract_env_vars_from_string("")
        assert result == []

    def test_env_var_with_filter(self):
        """Extract env var even when filter is applied."""
        template = "{{env.MY_VAR | upper}}"
        result = extract_env_vars_from_string(template)
        assert result == ["MY_VAR"]


class TestExtractRuntimeParamsFromString:
    """Test extracting runtime parameters from template strings."""

    def test_simple_runtime_param(self):
        """Extract a single runtime parameter."""
        template = "{{param}}"
        result = extract_runtime_params_from_string(template)
        assert result == ["param"]

    def test_multiple_runtime_params(self):
        """Extract multiple runtime parameters."""
        template = "{{param1}}_{{param2}}"
        result = extract_runtime_params_from_string(template)
        assert set(result) == {"param1", "param2"}

    def test_runtime_param_in_text(self):
        """Extract runtime param from template with surrounding text."""
        template = "prefix_{{user_id}}_suffix"
        result = extract_runtime_params_from_string(template)
        assert result == ["user_id"]

    def test_mixed_runtime_and_env_vars(self):
        """Extract only runtime params when mixed with env vars."""
        template = "{{user_id}}/{{env.API_KEY}}/{{endpoint}}"
        result = extract_runtime_params_from_string(template)
        assert set(result) == {"user_id", "endpoint"}

    def test_duplicate_runtime_params(self):
        """Duplicate params should be deduplicated."""
        template = "{{param}}_{{param}}"
        result = extract_runtime_params_from_string(template)
        assert result == ["param"]

    def test_no_runtime_params(self):
        """Return empty list when no runtime params present."""
        template = "{{env.MY_VAR}}"
        result = extract_runtime_params_from_string(template)
        assert result == []

    def test_empty_string(self):
        """Handle empty string."""
        result = extract_runtime_params_from_string("")
        assert result == []

    def test_no_template(self):
        """Handle plain string without templates."""
        result = extract_runtime_params_from_string("plain text")
        assert result == []

    def test_runtime_param_with_filter(self):
        """Extract runtime param even when filter is applied."""
        template = "{{my_param | upper}}"
        result = extract_runtime_params_from_string(template)
        assert result == ["my_param"]

    def test_excludes_env_object(self):
        """Should not extract 'env' as a runtime param."""
        template = "{{env.MY_VAR}}"
        result = extract_runtime_params_from_string(template)
        assert result == []

    def test_complex_template(self):
        """Extract params from complex template."""
        template = "https://{{domain}}/{{version}}/users/{{user_id}}"
        result = extract_runtime_params_from_string(template)
        assert set(result) == {"domain", "version", "user_id"}


class TestExtractEnvVars:
    """Test extracting environment variables from ConfigurableDict."""

    def test_with_env_var_config_object(self):
        """Extract env var from EnvVarConfig object."""
        spec = {"api_key": EnvVarConfig(env="API_KEY")}
        result = extract_env_vars(spec)
        assert result == ["API_KEY"]

    def test_with_multiple_env_var_config_objects(self):
        """Extract multiple env vars from EnvVarConfig objects."""
        spec = {
            "api_key": EnvVarConfig(env="API_KEY"),
            "region": EnvVarConfig(env="AWS_REGION"),
        }
        result = extract_env_vars(spec)
        assert set(result) == {"API_KEY", "AWS_REGION"}

    def test_with_template_string(self):
        """Extract env var from template string."""
        spec = {"url": "https://{{env.API_HOST}}/api"}
        result = extract_env_vars(spec)
        assert result == ["API_HOST"]

    def test_with_mixed_config(self):
        """Extract env vars from mixed EnvVarConfig and template strings."""
        spec = {
            "api_key": EnvVarConfig(env="API_KEY"),
            "url": "https://{{env.API_HOST}}/api",
            "region": EnvVarConfig(env="REGION"),
        }
        result = extract_env_vars(spec)
        assert set(result) == {"API_KEY", "API_HOST", "REGION"}

    def test_with_runtime_params_ignored(self):
        """Runtime params should be ignored."""
        spec = {
            "api_key": EnvVarConfig(env="API_KEY"),
            "user_id": RunTimeParam(param="user_id"),
            "url": "https://{{env.HOST}}/{{endpoint}}",
        }
        result = extract_env_vars(spec)
        assert set(result) == {"API_KEY", "HOST"}

    def test_with_plain_values_ignored(self):
        """Plain string values without templates should be ignored."""
        spec = {
            "api_key": EnvVarConfig(env="API_KEY"),
            "static_value": "plain text",
            "number": 42,
        }
        result = extract_env_vars(spec)
        assert result == ["API_KEY"]

    def test_empty_spec(self):
        """Handle empty spec."""
        result = extract_env_vars({})
        assert result == []

    def test_none_spec(self):
        """Handle None spec."""
        result = extract_env_vars(None)
        assert result == []

    def test_deduplication(self):
        """Duplicate env vars should be deduplicated."""
        spec = {
            "key1": EnvVarConfig(env="API_KEY"),
            "key2": "{{env.API_KEY}}",
            "key3": EnvVarConfig(env="API_KEY"),
        }
        result = extract_env_vars(spec)
        assert result == ["API_KEY"]


class TestExtractRuntimeParams:
    """Test extracting runtime parameters from ConfigurableDict."""

    def test_with_runtime_param_object(self):
        """Extract runtime param from RunTimeParam object."""
        spec = {"user_id": RunTimeParam(param="user_id")}
        result = extract_runtime_params(spec)
        assert result == ["user_id"]

    def test_with_runtime_param_with_type(self):
        """Extract runtime param from RunTimeParam with explicit type."""
        spec = {
            "user_id": RunTimeParam(param="user_id", value_type="str"),
            "count": RunTimeParam(param="count", value_type="int"),
            "price": RunTimeParam(param="price", value_type="float"),
        }
        result = extract_runtime_params(spec)
        assert set(result) == {"user_id", "count", "price"}

    def test_with_template_string(self):
        """Extract runtime param from template string."""
        spec = {"url": "https://api.com/users/{{user_id}}"}
        result = extract_runtime_params(spec)
        assert result == ["user_id"]

    def test_with_mixed_config(self):
        """Extract runtime params from mixed RunTimeParam and template strings."""
        spec = {
            "user_id": RunTimeParam(param="user_id", value_type="str"),
            "url": "https://{{domain}}/{{version}}/api",
            "count": RunTimeParam(param="count", value_type="int"),
        }
        result = extract_runtime_params(spec)
        assert set(result) == {"user_id", "domain", "version", "count"}

    def test_with_env_vars_ignored(self):
        """Environment vars should be ignored."""
        spec = {
            "user_id": RunTimeParam(param="user_id"),
            "api_key": EnvVarConfig(env="API_KEY"),
            "url": "https://{{domain}}/{{env.REGION}}/api",
        }
        result = extract_runtime_params(spec)
        assert set(result) == {"user_id", "domain"}

    def test_with_plain_values_ignored(self):
        """Plain values without templates should be ignored."""
        spec = {
            "user_id": RunTimeParam(param="user_id"),
            "static_value": "plain text",
            "number": 42,
        }
        result = extract_runtime_params(spec)
        assert result == ["user_id"]

    def test_empty_spec(self):
        """Handle empty spec."""
        result = extract_runtime_params({})
        assert result == []

    def test_none_spec(self):
        """Handle None spec."""
        result = extract_runtime_params(None)
        assert result == []

    def test_deduplication(self):
        """Duplicate runtime params should be deduplicated."""
        spec = {
            "param1": RunTimeParam(param="user_id"),
            "param2": "{{user_id}}",
            "param3": RunTimeParam(param="user_id", value_type="str"),
        }
        result = extract_runtime_params(spec)
        assert result == ["user_id"]

    def test_runtime_param_auto_type(self):
        """Test RunTimeParam with auto type (default)."""
        spec = {
            "param1": RunTimeParam(param="value1"),  # auto is default
            "param2": RunTimeParam(param="value2", value_type="auto"),
        }
        result = extract_runtime_params(spec)
        assert set(result) == {"value1", "value2"}


class TestConfigureFieldsWithDictCasting:
    """Test configure_fields with dictionary representations of RunTimeParam and EnvVarConfig."""

    def test_runtime_param_from_dict(self):
        """Should convert dict with 'param' key to RunTimeParam."""
        spec = {"user_id": {"param": "user_id", "value_type": "str"}}
        local_vars = {"user_id": "12345"}
        env_vars = {}

        result = configure_fields(spec, local_vars, env_vars)

        assert isinstance(result["user_id"], str)
        assert result["user_id"] == "12345"

    def test_env_var_config_from_dict(self):
        """Should convert dict with 'env' key to EnvVarConfig."""
        spec = {"api_key": {"env": "API_KEY"}}
        local_vars = {}
        env_vars = {"API_KEY": "secret123"}

        result = configure_fields(spec, local_vars, env_vars)

        assert isinstance(result["api_key"], str)
        assert result["api_key"] == "secret123"

    def test_runtime_param_dict_with_default_type(self):
        """Should handle RunTimeParam dict with default value_type (auto)."""
        spec = {"count": {"param": "count"}}  # value_type defaults to "auto"
        local_vars = {"count": "42"}
        env_vars = {}

        result = configure_fields(spec, local_vars, env_vars)

        assert isinstance(result["count"], int)
        assert result["count"] == 42

    def test_runtime_param_dict_with_int_type(self):
        """Should convert to int when value_type is 'int'."""
        spec = {"count": {"param": "count", "value_type": "int"}}
        local_vars = {"count": "99"}
        env_vars = {}

        result = configure_fields(spec, local_vars, env_vars)

        assert isinstance(result["count"], int)
        assert result["count"] == 99

    def test_runtime_param_dict_with_float_type(self):
        """Should convert to float when value_type is 'float'."""
        spec = {"price": {"param": "price", "value_type": "float"}}
        local_vars = {"price": "19.99"}
        env_vars = {}

        result = configure_fields(spec, local_vars, env_vars)

        assert isinstance(result["price"], float)
        assert result["price"] == 19.99

    def test_mixed_dict_and_object_representations(self):
        """Should handle mix of dict and object representations."""
        spec = {
            "user_id": {"param": "user_id", "value_type": "str"},  # dict
            "count": RunTimeParam(param="count", value_type="int"),  # object
            "api_key": {"env": "API_KEY"},  # dict
            "region": EnvVarConfig(env="REGION"),  # object
        }
        local_vars = {"user_id": "12345", "count": "42"}
        env_vars = {"API_KEY": "secret", "REGION": "us-west-2"}

        result = configure_fields(spec, local_vars, env_vars)

        assert result["user_id"] == "12345"
        assert isinstance(result["user_id"], str)

        assert result["count"] == 42
        assert isinstance(result["count"], int)

        assert result["api_key"] == "secret"
        assert isinstance(result["api_key"], str)

        assert result["region"] == "us-west-2"
        assert isinstance(result["region"], str)

    def test_invalid_dict_remains_dict(self):
        """Dicts that can't be converted should remain as dicts."""
        spec = {
            "config": {
                "some": "value",
                "other": "data",
            }  # Not a valid RunTimeParam or EnvVarConfig
        }
        local_vars = {}
        env_vars = {}

        result = configure_fields(spec, local_vars, env_vars)

        # Should remain as dict since it can't be converted
        assert isinstance(result["config"], dict)
        assert result["config"] == {"some": "value", "other": "data"}


class TestIsTemplateLike:
    """Test cases for the _is_template_like helper function."""

    def test_full_template_string(self):
        """Full template strings should be detected."""
        assert _is_template_like("{{var}}") is True
        assert _is_template_like("{{env.API_KEY}}") is True
        assert _is_template_like("{{user_id}}") is True
        assert _is_template_like("{{ var }}") is True
        assert _is_template_like("{{  env.API_KEY  }}") is True

    def test_template_at_start(self):
        """Templates at the start with text after should be detected."""
        assert _is_template_like("{{param1}} Value") is True
        assert _is_template_like("{{env.HOST}}/api/v1") is True
        assert _is_template_like("{{count}} items") is True

    def test_template_at_end(self):
        """Templates at the end with text before should be detected."""
        assert _is_template_like("Basic {{env.API_KEY}}") is True
        assert _is_template_like("User ID: {{user_id}}") is True
        assert _is_template_like("https://api.com/{{endpoint}}") is True

    def test_template_in_middle(self):
        """Templates in the middle with text on both sides should be detected."""
        assert _is_template_like("prefix {{var}} suffix") is True
        assert _is_template_like("https://{{domain}}/api") is True
        assert _is_template_like("Bearer {{env.TOKEN}}!") is True
        assert _is_template_like("prefix {{ var }} suffix") is True

    def test_multiple_templates(self):
        """Strings with multiple templates should be detected."""
        assert _is_template_like("{{var1}} middle {{var2}}") is True
        assert _is_template_like("{{env.HOST}}/{{version}}/{{endpoint}}") is True
        assert _is_template_like("{{first}} and {{second}} and {{third}}") is True

    def test_plain_text_no_templates(self):
        """Plain text without templates should not be detected."""
        assert _is_template_like("plain text") is False
        assert _is_template_like("no templates here") is False
        assert _is_template_like("just a string") is False
        assert _is_template_like("12345") is False
        assert _is_template_like("") is False

    def test_wrong_order_delimiters(self):
        """Wrong order delimiters should not be detected."""
        assert _is_template_like("}} {{") is False
        assert _is_template_like("}} text {{") is False
        assert _is_template_like("{{var") is False
        assert _is_template_like("var}}") is False
        assert _is_template_like("{{") is False
        assert _is_template_like("}}") is False
        assert _is_template_like("{var}") is False
        assert _is_template_like("{ var }") is False
