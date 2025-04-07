from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from vulkan_server import schemas
from vulkan_server.db import User, get_db
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
