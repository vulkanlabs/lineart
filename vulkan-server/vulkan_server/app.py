import asyncio
import os
from contextlib import asynccontextmanager

import requests
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from vulkan_server import exceptions, routers
from vulkan_server.backtest.daemon import BacktestDaemon
from vulkan_server.logger import init_logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        backtest_daemon = BacktestDaemon.from_env()
        asyncio.create_task(backtest_daemon.run_main())
        yield
    finally:
        tasks = asyncio.all_tasks()
        for task in tasks:
            task.cancel()


app = FastAPI(lifespan=lifespan)

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
app.include_router(routers.backfills.router)
app.include_router(routers.backtests.router)
app.include_router(routers.data.sources)
app.include_router(routers.data.broker)
app.include_router(routers.files.router)
app.include_router(routers.policies.router)
app.include_router(routers.policy_versions.router)
app.include_router(routers.projects.router)
app.include_router(routers.runs.router)
app.include_router(routers.users.router)


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
    user_id = response.json().get("id", None)

    if user_id is None:
        return JSONResponse(content="Unauthorized", status_code=401)

    # Create a new headers object with the user id entry.
    # We add this both to the headers and the scope for consistency.
    headers = request.headers.mutablecopy()
    headers.append("x-user-id", user_id)
    request._headers = headers
    request.scope["headers"] = request.headers.raw
    return await call_next(request)


class ErrorResponse(BaseModel):
    error_code: str
    message: str


@app.exception_handler(exceptions.VulkanServerException)
async def vulkan_server_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(error_code=exc.error_code, message=exc.msg).model_dump(),
    )
