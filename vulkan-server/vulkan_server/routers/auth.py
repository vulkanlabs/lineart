# vulkan-server/vulkan_server/routers/auth.py

import base64
import json
import urllib.parse

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse, RedirectResponse

# Assuming a dependency injection system for the service
from vulkan_engine.services.credential import CredentialService

from vulkan_server.dependencies import get_credential_service

router = APIRouter(
    prefix="/auth",
    tags=["auth"],
    responses={404: {"description": "Not found"}},
)


@router.get("/{service_name}/start")
def start_auth(
    service_name: str,
    request: Request,
    project_id: str | None = None,
    service: CredentialService = Depends(get_credential_service),
):
    """Initiates the OAuth2 flow for a given service."""
    try:
        # The redirect URI must be registered in your Google Cloud project
        # and should point to our callback endpoint.
        redirect_uri = request.url_for("auth_callback", service_name=service_name)

        result = service.start_oauth_flow(
            service_name=service_name,
            project_id=project_id,
            redirect_uri=str(redirect_uri),
        )
        return JSONResponse(content=result)
    except (NotImplementedError, ValueError) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{service_name}/callback", name="auth_callback")
def auth_callback(
    service_name: str,
    request: Request,
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
    project_id: str | None = None,
    service: CredentialService = Depends(get_credential_service),
):
    """Handles the callback from the OAuth provider."""
    frontend_url = f"{request.base_url.scheme}://{request.base_url.netloc}/"
    frontend_path = request.base_url.path
    if frontend_path:
        frontend_url += frontend_path

    if error:
        # Handle OAuth error - redirect to frontend with error
        return RedirectResponse(
            url=f"{frontend_url}?auth_error={error}", status_code=302
        )

    if not code or not state:
        # Redirect to frontend with error
        return RedirectResponse(
            url=f"{frontend_url}?auth_error=missing_parameters", status_code=302
        )

    try:
        # Get the redirect URI from the request
        redirect_uri = str(request.url_for("auth_callback", service_name=service_name))

        # Complete the OAuth flow
        tokens = service.complete_oauth_flow(
            service_name=service_name,
            authorization_code=code,
            state=state,
            project_id=project_id,
            redirect_uri=redirect_uri,
        )

        # Redirect to frontend with success and tokens
        token_param = base64.urlsafe_b64encode(json.dumps(tokens).encode()).decode()
        return RedirectResponse(
            url=f"{frontend_url}?auth_success=true&tokens={token_param}",
            status_code=302,
        )
    except Exception as e:
        # Redirect to frontend with error
        error_param = urllib.parse.quote(str(e))
        return RedirectResponse(
            url=f"{frontend_url}?auth_error={error_param}", status_code=302
        )
