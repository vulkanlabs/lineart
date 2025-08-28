import os

import httpx
from lineart_sdk import Lineart as LineartBaseClient

from lineart.auth import LoginContext, refresh_credentials, retrieve_credentials
from lineart.logging import init_logger

_DEFAULT_SERVER_URL = "http://34.69.177.85:6001"
_NO_CREDS_MSG = "No valid credentials found. Please run `vcli login` and try again."
_NO_PROJECT_ID_MSG = (
    "No project ID provided and VULKAN_PROJECT_ID environment variable is not set."
    " Please provide a project ID to interact with Vulkan services."
)


class Lineart(LineartBaseClient):
    def __init__(
        self,
        server_url: str | None = None,
        project_id: str | None = None,
        log_level: str = "DEBUG",
        **kwargs,
    ):
        logger = init_logger(__name__, log_level)
        if server_url is None:
            server_url = os.getenv("VULKAN_SERVER_URL", _DEFAULT_SERVER_URL)
            logger.debug(
                "VULKAN_SERVER_URL environment variable is not set, using default"
            )

        if server_url == _DEFAULT_SERVER_URL and project_id is None:
            project_id = os.getenv("VULKAN_PROJECT_ID")
            if project_id is None:
                logger.error(_NO_PROJECT_ID_MSG)
                raise ValueError(_NO_PROJECT_ID_MSG)

        auth_headers = _get_auth_headers(log_level)
        if auth_headers is None and server_url == _DEFAULT_SERVER_URL:
            logger.error(_NO_CREDS_MSG)
            raise ValueError(_NO_CREDS_MSG)

        if project_id is not None:
            server_url = f"{server_url}/projects/{project_id}"

        client = httpx.Client(headers=auth_headers, follow_redirects=True)
        super().__init__(server_url=server_url, client=client, **kwargs)
        self.project_id = project_id
        self.log_level = log_level


def _get_auth_headers(log_level: str) -> dict[str, str]:
    """Get authentication headers for API requests."""
    login_ctx = LoginContext(log_level=log_level)

    ok = refresh_credentials(login_ctx)
    if not ok:
        return None

    try:
        creds = retrieve_credentials()
    except FileNotFoundError:
        return None

    return {
        "x-stack-access-token": creds["accessToken"],
        "x-stack-refresh-token": creds["refreshToken"],
    }
