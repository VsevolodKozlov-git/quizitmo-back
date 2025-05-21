# app/schemas/file.py

from typing import List
from pydantic import BaseModel

class FileOut(BaseModel):
    id_file: int
    file_name: str

    model_config = {
        "from_attributes": True
    }

class RemoveFileRequest(BaseModel):
    id_file: int

    model_config = {
        "extra": "forbid"
    }
