from typing import Annotated

from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session

from vulkan_server.db import User, get_db


def get_user_id(
    x_user_id: Annotated[str, Header()],
    db: Session = Depends(get_db),
) -> str:
    user = db.query(User).filter_by(user_auth_id=x_user_id).first()
    if user is None:
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve user. Contact the administrator.",
        )
    return user.user_id
