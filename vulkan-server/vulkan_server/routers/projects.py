from typing import Annotated

from fastapi import APIRouter, Body, Depends, HTTPException
from sqlalchemy.orm import Session

from vulkan_server import schemas
from vulkan_server.db import Project, ProjectUser, User, get_db

router = APIRouter(
    prefix="/projects",
    tags=["projects"],
    responses={404: {"description": "Not found"}},
)


@router.post("/", response_model=schemas.Project)
def create_project(
    name: Annotated[str, Body(embed=True)],
    db: Session = Depends(get_db),
):
    project = Project(name=name)
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
        raise HTTPException(status_code=404, detail="User not found")

    project_user = ProjectUser(project_id=project_id, **config.model_dump())
    db.add(project_user)
    db.commit()
    return project_user


@router.get("/{project_id}/users", response_model=list[schemas.ProjectUser])
def get_project_users(
    project_id: str,
    db: Session = Depends(get_db),
):
    return db.query(ProjectUser).filter_by(project_id=project_id).all()
