from typing import Annotated
import os

from fastapi import Body, Depends, Header, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from vulkan.core.run import RunStatus
import requests

from vulkan_server import routers, schemas
from vulkan_server.db import DBSession, Run, StepMetadata, get_db
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
    if response.json()['id'] is None:
        return HTTPException(status_code=401, detail="Unauthorized")
    return await call_next(request)


@app.get("/users/me")
def read_users_me(
    x_stack_access_token: Annotated[str, Header()],
    x_stack_refresh_token: Annotated[str, Header()],
):
    url = "https://api.stack-auth.com/api/v1/users/me"
    headers = {
        "x-stack-access-type": "server",
        "x-stack-project-id": STACK_PROJECT_ID,
        "x-stack-secret-server-key": STACK_SECRET_SERVER_KEY,
        "x-stack-access-token": x_stack_access_token,
        "x-stack-refresh-token": x_stack_refresh_token,
    }
    response = requests.get(url, headers=headers)
    data = response.json()
    logger.info(data)
    return {"user": data}


@app.get("/runs/{run_id}", response_model=schemas.Run)
def get_run(run_id: int, db: Session = Depends(get_db)):
    run = db.query(Run).filter_by(run_id=run_id).first()
    if run is None:
        raise HTTPException(status_code=400, detail=f"Run {run_id} not found")
    return run


@app.put("/runs/{run_id}", response_model=schemas.Run)
def update_run(
    run_id: int,
    status: Annotated[str, Body()],
    result: Annotated[str, Body()],
    db: Session = Depends(get_db),
):
    run = db.query(Run).filter_by(run_id=run_id).first()
    if run is None:
        raise HTTPException(status_code=400, detail=f"Run {run_id} not found")

    try:
        status = RunStatus(status)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    run.status = status
    run.result = result
    db.commit()
    return run


@app.post("/runs/{run_id}/metadata")
def publish_metadata(run_id: int, config: schemas.StepMetadataBase):
    try:
        with DBSession() as db:
            args = {"run_id": run_id, **config.model_dump()}
            meta = StepMetadata(**args)
            db.add(meta)
            db.commit()
            return {"status": "success"}
    except KeyError as e:
        raise HTTPException(status_code=400, detail=e)
    except Exception as e:
        raise HTTPException(status_code=500, detail=e)
