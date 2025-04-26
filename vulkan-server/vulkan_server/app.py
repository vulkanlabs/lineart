import os

from fastapi import FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from vulkan_server import exceptions, routers
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
app.include_router(routers.backfills.router)
app.include_router(routers.backtests.router)
app.include_router(routers.data.sources)
app.include_router(routers.data.broker)
app.include_router(routers.files.router)
app.include_router(routers.policies.router)
app.include_router(routers.policy_versions.router)
app.include_router(routers.runs.router)
app.include_router(routers.users.router)


logger = init_logger("vulkan_server")


STACK_PROJECT_ID = os.getenv("STACK_PROJECT_ID")
STACK_SECRET_SERVER_KEY = os.getenv("STACK_SECRET_SERVER_KEY")


class ErrorResponse(BaseModel):
    error: str
    message: str


@app.exception_handler(exceptions.VulkanServerException)
async def vulkan_server_exception_handler(
    request: Request,
    exc: exceptions.VulkanServerException,
):
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(error=exc.error_code, message=exc.msg).model_dump(),
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=jsonable_encoder({"detail": exc.errors(), "body": exc.body}),
    )
