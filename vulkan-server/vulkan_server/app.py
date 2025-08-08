from fastapi import FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute
from pydantic import BaseModel
from vulkan_engine import exceptions
from vulkan_engine.logger import init_logger

from vulkan_server import routers


def custom_generate_unique_id(route: APIRoute) -> str:
    """
    Generate clean operation IDs using just the function name.
    This results in cleaner method names in generated API clients.
    """
    return route.name


app = FastAPI(generate_unique_id_function=custom_generate_unique_id)

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
app.include_router(routers.data.router)
app.include_router(routers.internal.router)
app.include_router(routers.policies.router)
app.include_router(routers.policy_versions.router)
app.include_router(routers.runs.router)
app.include_router(routers.auth.router)


logger = init_logger("vulkan_server")


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
