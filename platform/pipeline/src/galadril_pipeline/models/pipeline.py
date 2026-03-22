from pydantic import BaseModel
from typing import List, Dict, Any, Optional


class PipelineStep(BaseModel):
    step: str
    type: str
    model: Optional[str] = None
    artifact_path: Optional[str] = None
    input_from: List[str]
    params: Optional[Dict[str, Any]] = None
