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
    configure_fields,
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

    def test_runtime_param_with_bool_type(self):
        """RunTimeParam with value_type='bool' converts to bool."""
        spec = {"is_active": RunTimeParam(param="active_flag")}
        local_vars = {"active_flag": "True"}
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
            "is_active": RunTimeParam(param="active_flag", value_type="bool"),
            "api_key": EnvVarConfig(env="API_KEY"),
        }
        local_vars = {
            "user_tax_id": "12345678901",
            "num_items": "42",
            "amount": "19.99",
            "active_flag": "True",
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
