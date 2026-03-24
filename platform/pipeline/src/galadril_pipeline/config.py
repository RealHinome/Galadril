from pydantic import BaseModel
from typing import List
from galadril_pipeline.models.connectors import Connectors
from galadril_pipeline.models.sources import Source
from galadril_pipeline.models.pipeline import PipelineStep


class PipelineConfig(BaseModel):
    name: str
    connectors: Connectors
    sources: List[Source]
    pipeline: List[PipelineStep]
