"""
Validation models for vulkan-engine.

This module provides Pydantic models for validating input parameters
and ensuring data integrity across the application.
"""

from typing import List
from uuid import UUID

from pydantic import BaseModel, UUID4, ValidationError


class ResourceIdModel(BaseModel):
    """Base model for resource ID validation."""
    resource_id: UUID4


class DataSourceIdModel(ResourceIdModel):
    """Model for validating data source IDs."""
    data_source_id: UUID4


class PolicyIdModel(ResourceIdModel):
    """Model for validating policy IDs."""
    policy_id: UUID4


class PolicyVersionIdModel(ResourceIdModel):
    """Model for validating policy version IDs."""
    policy_version_id: UUID4


class RunIdModel(ResourceIdModel):
    """Model for validating run IDs."""
    run_id: UUID4


class ComponentIdModel(ResourceIdModel):
    """Model for validating component IDs."""
    component_id: UUID4


class WorkflowIdModel(ResourceIdModel):
    """Model for validating workflow IDs."""
    workflow_id: UUID4


class ProjectIdModel(BaseModel):
    """Model for validating project IDs (optional)."""
    project_id: UUID4 | None = None


def validate_uuid(uuid_string: str, resource_type: str = "resource") -> UUID:
    """
    Validate a UUID string and return UUID object.
    
    Args:
        uuid_string: String to validate as UUID
        resource_type: Type of resource for error message
        
    Returns:
        UUID object if valid
        
    Raises:
        ValueError: If UUID is invalid
    """
    try:
        return UUID(uuid_string)
    except ValueError:
        raise ValueError(f"Invalid {resource_type} ID format: {uuid_string}")


def validate_uuid_list(uuid_strings: List[str], resource_type: str = "resource") -> List[UUID]:
    """
    Validate a list of UUID strings and return list of UUID objects.
    
    Args:
        uuid_strings: List of strings to validate as UUIDs
        resource_type: Type of resource for error message
        
    Returns:
        List of UUID objects if all valid
        
    Raises:
        ValueError: If any UUID is invalid
    """
    try:
        return [UUID(uuid_str) for uuid_str in uuid_strings]
    except ValueError as e:
        raise ValueError(f"Invalid {resource_type} ID format in list: {e}")


def validate_optional_uuid(uuid_string: str | None, resource_type: str = "resource") -> UUID | None:
    """
    Validate an optional UUID string and return UUID object or None.
    
    Args:
        uuid_string: String to validate as UUID or None
        resource_type: Type of resource for error message
        
    Returns:
        UUID object if valid, None if None
        
    Raises:
        ValueError: If UUID is invalid
    """
    if uuid_string is None:
        return None
    return validate_uuid(uuid_string, resource_type) 