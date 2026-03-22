from pydantic import BaseModel
from typing import Optional


class Source(BaseModel):
    id: str
    topic: str
    schema_path: Optional[str] = None
