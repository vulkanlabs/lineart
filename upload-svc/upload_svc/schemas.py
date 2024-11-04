from pydantic import BaseModel


class FileIdentifier(BaseModel):
    file_path: str
