from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional


class ColumnMapping(BaseModel):
    column_name: str
    data: Optional[str] = None


class StepParams(BaseModel):
    threshold: Optional[float] = None
    table_name: Optional[str] = None
    columns: Optional[List[ColumnMapping]] = None
    limit: Optional[int] = None
    on_no_match: Optional[str] = None

    # Allow dynamic parameters.
    model_config = {"extra": "allow"}


class PipelineStep(BaseModel):
    step: str
    type: str
    connector: Optional[str] = None
    model: Optional[str] = None
    artifact_path: Optional[str] = None
    input_from: List[str]
    params: Optional[StepParams] = None
