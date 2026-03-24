from __future__ import annotations

from typing import Any

from galadril_pipeline.config import PipelineConfig
from galadril_pipeline.models.pipeline import PipelineStep
from pipeline.model_loader import build_model
from pipeline.duckdb import run_duckdb_aggregation


class DynamicPipelineExecutor:
    def __init__(self, config: PipelineConfig) -> None:
        self.config = config
        self.outputs: dict[str, list[dict[str, Any]]] = {}

    def _resolve_input(self, step: PipelineStep) -> list[dict[str, Any]]:
        inputs: list[dict[str, Any]] = []
        for src in step.input_from:
            inputs.extend(self.outputs.get(src, []))
        return inputs

    def register_source_batch(
        self, source_id: str, batch: list[dict[str, Any]]
    ) -> None:
        self.outputs[source_id] = batch

    def run_step(self, step: PipelineStep) -> list[dict[str, Any]]:
        data = self._resolve_input(step)

        if step.duckdb and step.duckdb.enabled and step.duckdb.query:
            data = run_duckdb_aggregation(data, step.duckdb.query)

        model = build_model(
            step.model,
            artifact_path=step.artifact_path,
            **step.params,
        )

        result = model.predict(data)
        if isinstance(result, dict):
            result = [result]
        self.outputs[step.step] = result
        return result

    def run(self) -> dict[str, list[dict[str, Any]]]:
        for step in self.config.pipeline:
            self.run_step(step)
        return self.outputs
