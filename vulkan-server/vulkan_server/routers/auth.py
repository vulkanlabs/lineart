# vulkan-server/vulkan_server/routers/auth.py

import urllib.parse

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse

# Assuming a dependency injection system for the service
from vulkan_engine.services.credential.credential import CredentialService
from vulkan_engine.services.credential.schemas import (
    AuthDisconnectResponse,
    AuthStartResponse,
    AuthUserInfoResponse,
)

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
) -> AuthStartResponse:
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
        return result
    except (NotImplementedError, ValueError) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{service_name}/user_info")
def get_user_info(
    service_name: str,
    project_id: str | None = None,
    service: CredentialService = Depends(get_credential_service),
) -> AuthUserInfoResponse:
    try:
        user_info = service.get_user_info(
            service_name=service_name,
            project_id=project_id,
        )
        return user_info
    except (NotImplementedError, ValueError) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{service_name}/disconnect")
def disconnect(
    service_name: str,
    project_id: str | None = None,
    service: CredentialService = Depends(get_credential_service),
) -> AuthDisconnectResponse:
    service.disconnect(service_name=service_name, project_id=project_id)
    return AuthDisconnectResponse(message="Disconnected successfully")


# TODO: This is still broken: the redirects are not working.
# We may want to just point to a "done" page that says whether or not
# the auth was successful.
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

        service.logger.system.info(f"Tokens: {tokens}")

        # Notify the frontend that the token has been created.
        return RedirectResponse(
            url=f"{frontend_url}?auth_success=true", status_code=302
        )
    except Exception as e:
        # Redirect to frontend with error
        error_param = urllib.parse.quote(str(e))
        return RedirectResponse(
            url=f"{frontend_url}?auth_error={error_param}", status_code=302
        )
