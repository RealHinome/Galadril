import yaml
from pathlib import Path
from galadril_pipeline.config import PipelineConfig
from galadril_pipeline.graph import PipelineGraph


class PipelineParser:
    @staticmethod
    def from_yaml(file_path: str | Path) -> PipelineGraph:
        """Load and validate YAML config. Returns pipeline graph."""
        with open(file_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        config = PipelineConfig(**data)

        return PipelineGraph(config)
