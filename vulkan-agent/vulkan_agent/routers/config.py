"""Configuration router for agent settings management."""

from fastapi import APIRouter, HTTPException, status

from ..agent import refresh_global_agent
from ..config import config_manager
from ..schemas import (
    AgentConfigRequest,
    AgentConfigResponse,
    AgentConfigValidationRequest,
    AgentConfigValidationResponse,
)

router = APIRouter(prefix="/api/config", tags=["configuration"])


@router.get("/", response_model=AgentConfigResponse)
async def get_config():
    """Get current agent configuration."""
    config = config_manager.get_config()

    if config is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent configuration not found. Please configure the agent first.",
        )

    return config


@router.post("/", response_model=AgentConfigResponse)
async def update_config(config_request: AgentConfigRequest):
    """Update agent configuration."""
    try:
        # Validate the configuration first
        config_manager.validate_config(
            config_request.provider, config_request.api_key, config_request.model
        )

        # Update configuration
        updated_config = config_manager.update_config(config_request)

        # Refresh the global agent to use the new configuration
        refresh_global_agent()

        return updated_config

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update configuration: {str(e)}",
        )


@router.post("/validate", response_model=AgentConfigValidationResponse)
async def validate_config(validation_request: AgentConfigValidationRequest):
    """Validate API key and configuration without saving."""
    try:
        config_manager.validate_config(
            validation_request.provider,
            validation_request.api_key,
            validation_request.model,
        )

        return AgentConfigValidationResponse(
            valid=True,
            message="API key is valid and connection successful",
            provider=validation_request.provider,
        )

    except ValueError as e:
        return AgentConfigValidationResponse(
            valid=False,
            message=str(e),
            provider=validation_request.provider,
        )
    except Exception as e:
        return AgentConfigValidationResponse(
            valid=False,
            message=f"Validation error: {str(e)}",
            provider=validation_request.provider,
        )


@router.get("/status")
async def get_config_status():
    """Get agent configuration status."""
    return {
        "configured": config_manager.is_configured(),
        "message": "Agent is ready"
        if config_manager.is_configured()
        else "Agent needs configuration",
    }
