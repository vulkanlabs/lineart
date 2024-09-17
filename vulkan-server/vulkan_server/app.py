import os

import requests
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware

from vulkan_server import routers
from vulkan_server.logger import init_logger

app = FastAPI()

origins = [
    "http://127.0.0.1",
    "http://0.0.0.0",
    "http://localhost",
    "http://localhost:8080",
    "http://host.docker.internal",
    "http://host.docker.internal:8080",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(routers.components.router)
app.include_router(routers.policies.router)
app.include_router(routers.policy_versions.router)


logger = init_logger("vulkan_server")


STACK_PROJECT_ID = os.getenv("STACK_PROJECT_ID")
STACK_SECRET_SERVER_KEY = os.getenv("STACK_SECRET_SERVER_KEY")


@app.middleware("http")
async def auth_user(request: Request, call_next):
    x_stack_access_token = request.headers.get("x-stack-access-token")
    x_stack_refresh_token = request.headers.get("x-stack-refresh-token")
    # TODO: This leaves some endpoints unprotected. We should add a list of
    # endpoints that should be authenticated through a diffent method (i.e.,
    # for internal API calls).
    if not x_stack_access_token or not x_stack_refresh_token:
        return await call_next(request)

    url = "https://api.stack-auth.com/api/v1/users/me"
    headers = {
        "x-stack-access-type": "server",
        "x-stack-project-id": STACK_PROJECT_ID,
        "x-stack-secret-server-key": STACK_SECRET_SERVER_KEY,
        "x-stack-access-token": x_stack_access_token,
        "x-stack-refresh-token": x_stack_refresh_token,
    }
    response = requests.get(url, headers=headers)
    user_id = response.json()["id"]

    if user_id is None:
        raise HTTPException(status_code=401, detail="Unauthorized")
    logger.info(request.headers)
    # Create a new headers object with the user id entry.
    # We add this both to the headers and the scope for consistency.
    headers = request.headers.mutablecopy()
    headers.append("x-user-id", user_id)
    request._headers = headers
    request.scope["headers"] = request.headers.raw
    return await call_next(request)
