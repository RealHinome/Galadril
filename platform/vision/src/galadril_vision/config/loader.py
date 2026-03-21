from __future__ import annotations

from pathlib import Path
import yaml

from galadril_vision.config.schema import PipelineYamlConfig


def load_pipeline_config(path: str | Path) -> PipelineYamlConfig:
    p = Path(path)
    raw = yaml.safe_load(p.read_text(encoding="utf-8"))
    return PipelineYamlConfig.model_validate(raw)
