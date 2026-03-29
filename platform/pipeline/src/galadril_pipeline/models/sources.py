from pydantic import BaseModel
from typing import Optional


class Source(BaseModel):
    id: str
    topic: str
    match_pattern: Optional[str] = None
    schema_path: Optional[str] = None
