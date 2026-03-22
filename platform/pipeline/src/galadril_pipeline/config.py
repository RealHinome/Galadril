from pydantic import BaseModel
from typing import List
from .models.connectors import Connectors
from .models.sources import Source
from .models.pipeline import PipelineStep

class PipelineConfig(BaseModel):
    name: str
    connectors: Connectors
    sources: List[Source]
    pipeline: List[PipelineStep]
