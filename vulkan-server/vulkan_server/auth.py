from typing import Annotated
from uuid import UUID

from fastapi import Depends, Header, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from vulkan_server.db import ProjectUser, Role, User, get_db


# TODO: For now, we are equating project_id with user_id. Eventually, we'll
# allow users to be part of multiple projects and have a more refined
# role-based access control (including support for Teams).
def get_project_id(
    x_user_id: Annotated[str, Header()],
    db: Session = Depends(get_db),
) -> str:
    project_user = (
        db.query(ProjectUser).join(User).filter(User.user_auth_id == x_user_id).first()
    )
    if project_user is None:
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve user. Contact the administrator.",
        )
    return str(project_user.project_id)


class AuthContext(BaseModel):
    project_id: UUID
    user_id: UUID
    user_role: Role


def get_auth_context(
    x_user_id: Annotated[str, Header()],
    db: Session = Depends(get_db),
) -> AuthContext:
    project_user = (
        db.query(ProjectUser).join(User).filter(User.user_auth_id == x_user_id).first()
    )
    if project_user is None:
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve user. Contact the administrator.",
        )
    return AuthContext(
        project_id=project_user.project_id,
        user_id=project_user.user_id,
        user_role=project_user.role,
    )
