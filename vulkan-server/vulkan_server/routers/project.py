import json
from typing import Annotated

import requests
from fastapi import APIRouter, Body, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from vulkan_server import definitions, schemas
from vulkan_server.auth import get_project_id
from vulkan_server.db import (
    User,
    Project,
    ProjectUser,
    get_db,
)
from vulkan_server.logger import init_logger

logger = init_logger("project")
router = APIRouter(
    prefix="/project",
    tags=["project"],
    responses={404: {"description": "Not found"}},
)


@router.post("/", response_model=schemas.Project)
def create_project(
    project: schemas.ProjectBase,
    db: Session = Depends(get_db),
):
    project = Project(**project.model_dump())
    db.add(project)
    db.commit()
    return project


@router.post("/{project_id}/users", response_model=schemas.ProjectUser)
def add_user_to_project(
    project_id: str,
    config: schemas.ProjectUserCreate,
    db: Session = Depends(get_db),
):
    user = db.query(User).filter_by(user_id=config.user_id).first()
    if not user:
        raise HTTPException(status_code=400, detail="User not found")

    project_user = ProjectUser(project_id=project_id, **config.model_dump())
    db.add(project_user)
    db.commit()
    return project_user
