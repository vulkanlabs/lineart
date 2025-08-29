import configparser
import os
from pathlib import Path

import httpx
from lineart_sdk import Lineart as LineartBaseClient
from requests.exceptions import ConnectionError

from lineart.auth.login import LoginContext, refresh_credentials, retrieve_credentials
from lineart.logging import init_logger

# Assuming these imports exist from your project structure
_DEFAULT_SERVER_URL = "http://34.69.177.85:6001"
_NO_CREDS_MSG = "No valid credentials found. Please run `vcli login` and try again."
_NO_PROJECT_ID_MSG = (
    "No project ID provided and VULKAN_PROJECT_ID environment variable is not set."
    " Please provide a project ID to interact with Vulkan services."
)

# --- Configuration Management ---
# Defines the path for the configuration file and key names.
CONFIG_DIR = Path.home() / ".config" / "vulkan"
CONFIG_FILE = CONFIG_DIR / "config.ini"
CONFIG_SECTION = "default"
PROJECT_ID_KEY = "VULKAN_PROJECT_ID"


class Lineart(LineartBaseClient):
    def __init__(
        self,
        server_url: str | None = None,
        project_id: str | None = None,
        log_level: str = "INFO",
        **kwargs,
    ):
        """Client for interacting with the Lineart API.

        Args:
        -----
            server_url (str | None): The base URL of the Lineart server. If None,
                it will be read from the VULKAN_SERVER_URL environment variable.
                Leave empty to use the default server URL.
            project_id (str | None): The project ID to scope API requests. If None,
                it will be read from the VULKAN_PROJECT_ID environment variable.
                Required if using the default server URL.
            log_level (str): The logging level. Defaults to "INFO".

        Raises:
        ------
            ValueError: When using the Vulkan platform, if no project ID is
                provided or if no valid credentials are found.
        """
        logger = init_logger(__name__, log_level)
        if server_url is None:
            server_url = os.getenv("VULKAN_SERVER_URL", _DEFAULT_SERVER_URL)
            logger.debug(
                "VULKAN_SERVER_URL environment variable is not set, using default"
            )

        if server_url == _DEFAULT_SERVER_URL and project_id is None:
            project_id = os.getenv("VULKAN_PROJECT_ID") or self._get_project_id()
            if project_id is None:
                logger.warning(_NO_PROJECT_ID_MSG)

        auth_headers = _get_auth_headers(log_level)
        if auth_headers is None and server_url == _DEFAULT_SERVER_URL:
            logger.error(_NO_CREDS_MSG)
            raise ValueError(_NO_CREDS_MSG)

        if project_id is not None:
            server_url = f"{server_url}/projects/{project_id}"

        client = httpx.Client(headers=auth_headers, follow_redirects=True)
        super().__init__(server_url=server_url, client=client, **kwargs)
        self.server_url = server_url
        self.project_id = project_id
        self.log_level = log_level

    def _save_project_id(self, project_id: str):
        """Saves the project ID to the config file."""
        # Ensure the directory exists
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        config = configparser.ConfigParser()

        # Read existing config to avoid overwriting other values
        if CONFIG_FILE.exists():
            config.read(CONFIG_FILE)

        if CONFIG_SECTION not in config:
            config[CONFIG_SECTION] = {}

        config[CONFIG_SECTION][PROJECT_ID_KEY] = project_id

        with open(CONFIG_FILE, "w") as configfile:
            config.write(configfile)

    def _get_project_id(self) -> str | None:
        """Retrieves the project ID from the config file."""
        if not CONFIG_FILE.exists():
            return None

        config = configparser.ConfigParser()
        config.read(CONFIG_FILE)

        return config.get(CONFIG_SECTION, PROJECT_ID_KEY, fallback=None)


def _get_auth_headers(log_level: str) -> dict[str, str]:
    """Get authentication headers for API requests."""
    login_ctx = LoginContext(log_level=log_level)

    try:
        ok = refresh_credentials(login_ctx)
        if not ok:
            return None
        creds = retrieve_credentials()
    except (FileNotFoundError, ConnectionError):
        return None

    return {
        "x-stack-access-token": creds["accessToken"],
        "x-stack-refresh-token": creds["refreshToken"],
    }
