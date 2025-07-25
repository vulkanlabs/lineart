# vulkan-server/vulkan_server/routers/auth.py

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse

# Assuming a dependency injection system for the service
from vulkan_engine.services.credential import CredentialService

from ..dependencies import get_credential_service  # This dependency needs to be created

router = APIRouter()


@router.get("/api/v1/auth/{service_name}/start")
def start_auth(
    service_name: str,
    request: Request,
    # A placeholder for getting the current user's ID
    # In a real app, this would come from an authentication dependency
    user_id: str = "user_placeholder_123",
    service: CredentialService = Depends(get_credential_service),
):
    """Initiates the OAuth2 flow for a given service."""
    try:
        # The redirect URI must be registered in your Google Cloud project
        # and should point to our callback endpoint.
        redirect_uri = request.url_for("auth_callback", service_name=service_name)

        result = service.start_oauth_flow(
            service_name=service_name, user_id=user_id, redirect_uri=str(redirect_uri)
        )
        return JSONResponse(content=result)
    except (NotImplementedError, ValueError) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/api/v1/auth/{service_name}/callback", name="auth_callback")
def auth_callback(service_name: str, request: Request):
    """Handles the callback from the OAuth provider."""
    # This is a placeholder for the next step of implementation.
    # It will receive the 'code' and 'state' from Google.
    return {
        "status": "callback received",
        "service": service_name,
        "params": request.query_params,
    }
