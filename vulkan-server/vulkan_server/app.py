from typing import Annotated

from fastapi import Body, Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from vulkan.core.run import RunStatus

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
