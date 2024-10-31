from uuid import UUID

from pydantic import BaseModel


class FileIdentifier(BaseModel):
    file_id: UUID
    file_path: str
