# vulkan-engine/vulkan_engine/services/credential.py

import base64
import json
import os
from typing import Any, Dict

import requests
from sqlalchemy.orm import Session
from vulkan_engine.services.base import BaseService
from vulkan_engine.services.credential.schemas import (
    AuthCompleteResponse,
    AuthStartResponse,
    AuthUserInfoResponse,
)

# Placeholder for a more robust session management solution
SESSION_CACHE = {}


GOOGLE_OAUTH_SCOPES = [
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/spreadsheets.readonly",
]


class CredentialService(BaseService):
    """Service for handling OAuth2 credential flows and management."""

    def __init__(self, db: Session):
        super().__init__(db)

    def _get_google_credentials(self) -> Dict[str, Any]:
        """Loads and parses the Google credentials from the environment variable."""
        b64_creds = os.environ.get("GOOGLE_OAUTH_CREDENTIALS_B64")
        if not b64_creds:
            raise ValueError(
                "GOOGLE_OAUTH_CREDENTIALS_B64 environment variable not set."
            )

        try:
            json_creds = base64.b64decode(b64_creds).decode("utf-8")
            creds = json.loads(json_creds)
            if (
                "web" not in creds
                or "client_id" not in creds["web"]
                or "client_secret" not in creds["web"]
            ):
                raise ValueError("Invalid Google credentials format.")
            return creds["web"]
        except (json.JSONDecodeError, TypeError, ValueError) as e:
            raise ValueError(f"Failed to parse Google credentials: {e}") from e

    def start_oauth_flow(
        self, service_name: str, project_id: str | None, redirect_uri: str
    ) -> AuthStartResponse:
        """Constructs the authorization URL for the given service."""
        if service_name.lower() != "google":
            raise NotImplementedError(f"Service '{service_name}' is not supported.")

        creds = self._get_google_credentials()
        client_id = creds["client_id"]

        # Generate a state token for CSRF protection
        state = os.urandom(16).hex()
        SESSION_CACHE[project_id] = {"state": state}  # Store state against project_id

        # Define the required scopes
        scopes = GOOGLE_OAUTH_SCOPES
        scope_str = " ".join(scopes)

        auth_url = (
            f"https://accounts.google.com/o/oauth2/v2/auth?"
            f"client_id={client_id}&"
            f"redirect_uri={redirect_uri}&"
            f"response_type=code&"
            f"scope={scope_str}&"
            f"access_type=offline&"
            f"prompt=consent&"
            f"state={state}"
        )

        return {"authorization_url": auth_url}

    def complete_oauth_flow(
        self,
        service_name: str,
        authorization_code: str,
        state: str,
        project_id: str | None,
        redirect_uri: str,
    ) -> AuthCompleteResponse:
        """Completes the OAuth2 flow by exchanging the authorization code for tokens."""
        if service_name.lower() != "google":
            raise NotImplementedError(f"Service '{service_name}' is not supported.")

        # Verify state token for CSRF protection
        if (
            project_id not in SESSION_CACHE
            or SESSION_CACHE[project_id].get("state") != state
        ):
            raise ValueError("Invalid state token")

        creds = self._get_google_credentials()
        client_id = creds["client_id"]
        client_secret = creds["client_secret"]

        # Exchange authorization code for tokens

        token_url = "https://oauth2.googleapis.com/token"
        token_data = {
            "client_id": client_id,
            "client_secret": client_secret,
            "code": authorization_code,
            "grant_type": "authorization_code",
            "redirect_uri": redirect_uri,
        }

        response = requests.post(token_url, data=token_data)
        if not response.ok:
            raise ValueError(f"Failed to exchange code for tokens: {response.text}")

        tokens = response.json()

        # Store tokens in session cache (in a real implementation, this would be stored securely)
        SESSION_CACHE[project_id]["tokens"] = tokens

        return {
            "access_token": tokens.get("access_token"),
            "refresh_token": tokens.get("refresh_token"),
            "expires_in": tokens.get("expires_in"),
            "token_type": tokens.get("token_type"),
        }

    def get_user_info(
        self, service_name: str, project_id: str | None
    ) -> AuthUserInfoResponse:
        if service_name.lower() != "google":
            raise NotImplementedError(f"Service '{service_name}' is not supported.")

        msg = f"Failed to retrieve tokens for project_id {project_id}"
        project_id_cache = SESSION_CACHE.get(project_id)
        if project_id_cache is None:
            raise ValueError(msg)

        tokens = project_id_cache.get("tokens")
        if tokens is None:
            raise ValueError(msg)

        access_token = tokens.get("access_token")
        response = requests.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={
                "Authorization": f"Bearer {access_token}",
            },
        )
        if response.status_code != 200:
            raise ValueError(msg)

        user_info = response.json()
        return user_info

    def disconnect(self, service_name: str, project_id: str | None) -> None:
        if service_name.lower() != "google":
            raise NotImplementedError(f"Service '{service_name}' is not supported.")

        if project_id not in SESSION_CACHE:
            raise ValueError(f"Project {project_id} not found in session cache")

        del SESSION_CACHE[project_id]
