"""
Authentication credential type constants for Data Sources.

This module defines the valid credential types that can be used
for authenticating with external data sources.
"""

from enum import Enum


class CredentialType(str, Enum):
    """Valid credential types for data source authentication."""

    CLIENT_ID = "CLIENT_ID"
    CLIENT_SECRET = "CLIENT_SECRET"
    USERNAME = "USERNAME"
    PASSWORD = "PASSWORD"


def validate_no_reserved_credentials_in_templates(
    env_var_names: set[str] | list[str],
    error_context: str = "templates",
) -> None:
    """
    Validates that reserved credential names are not used in templates

    Reserved credential names (CLIENT_ID, CLIENT_SECRET, USERNAME, PASSWORD)
    are restricted to the credentials endpoint and cannot be used in
    environment variables or templates

    Args:
        env_var_names: Set or list of environment variable names to check
        error_context: Context description for error message (default: "templates")

    Raises:
        ValueError: If any reserved credential names are found

    Example:
        validate_no_reserved_credentials_in_templates(["API_KEY", "CLIENT_ID"])
        ValueError: Reserved credential names cannot be used in templates: CLIENT_ID
    """
    if isinstance(env_var_names, list):
        env_var_names = set(env_var_names)

    conflicts = {name for name in env_var_names if name in CredentialType}
    if conflicts:
        raise ValueError(
            f"Reserved credential names cannot be used in {error_context}: {', '.join(sorted(conflicts))}. "
            f"These names are reserved for authentication only: {', '.join(CredentialType)}. "
            f"Please use the /credentials endpoint to set these values."
        )


def validate_credential_type(credential_type: str) -> None:
    """
    Validates that a credential type is valid

    Args:
        credential_type: Credential type to validate

    Raises:
        ValueError: If credential type is invalid

    Example:
        validate_credential_type("CLIENT_ID")
        validate_credential_type("INVALID")
        ValueError: Invalid credential_type: INVALID
    """
    if credential_type not in CredentialType:
        raise ValueError(
            f"Invalid credential_type: {credential_type}. "
            f"Must be one of: {', '.join(CredentialType)}"
        )
