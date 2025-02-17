from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from vulkan_server import schemas
from vulkan_server.auth import get_project_id
from vulkan_server.db import ProjectUser, User, get_db
from vulkan_server.logger import init_logger

logger = init_logger("users")
router = APIRouter(
    prefix="/users",
    tags=["users"],
    responses={404: {"description": "Not found"}},
)


@router.post("/", response_model=schemas.User)
def create_user(
    config: schemas.UserBase,
    db: Session = Depends(get_db),
):
    user = User(**config.model_dump())
    db.add(user)
    db.commit()
    return user


@router.get("/{user_auth_id}", response_model=schemas.ProjectUser)
def get_user_project(
    user_auth_id: str,
    project_id: str = Depends(get_project_id),
    db: Session = Depends(get_db),
):
    q = (
        select(ProjectUser)
        .join(User)
        .filter(
            (User.user_auth_id == user_auth_id) & (ProjectUser.project_id == project_id)
        )
    )
    project_user = db.execute(q).scalars().first()
    if project_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return project_user
