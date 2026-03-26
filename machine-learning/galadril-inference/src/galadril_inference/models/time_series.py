"""Time series forecasting model powered by Google's TimesFM."""

from __future__ import annotations

from typing import Any

import numpy as np
import structlog

from galadril_inference.common.exceptions import (
    ModelLoadError,
    SchemaValidationError,
)
from galadril_inference.common.types import (
    ModelMeta,
    PredictionRequest,
    PredictionResult,
)
from galadril_inference.models.base import BaseModel

logger = structlog.get_logger(__name__)

_MODEL_NAME = "timesfm_forecast"
_MODEL_VERSION = "1.0.0"


class TimesFMModel(BaseModel):
    """Google TimesFM 2.5 200m model for time series forecasting."""

    def __init__(self) -> None:
        self._model: Any | None = None

    def meta(self) -> ModelMeta:
        return ModelMeta(
            name=_MODEL_NAME,
            version=_MODEL_VERSION,
            description="Zero-shot time series forecasting using google/timesfm-2.5-200m-pytorch.",
            tags={
                "domain": "time_series",
                "backend": "timesfm",
                "framework": "pytorch",
            },
        )

    def load(self, artifact_path: str) -> None:
        """Load the TimesFM model."""
        try:
            import timesfm
            import torch
        except ImportError as exc:
            raise ModelLoadError(
                _MODEL_NAME,
                "timesfm or torch is not installed.",
            ) from exc

        try:
            torch.set_float32_matmul_precision("high")

            self._model = timesfm.TimesFM_2p5_200M_torch.from_pretrained(
                "google/timesfm-2.5-200m-pytorch"
            )

            # TODO: custom config.
            self._model.compile(
                timesfm.ForecastConfig(
                    max_context=15000,
                    max_horizon=1000,
                    use_continuous_quantile_head=True,
                    fix_quantile_crossing=True,
                    infer_is_positive=False,
                )
            )

            logger.info("model_loaded", model_name=_MODEL_NAME)
        except Exception as exc:
            raise ModelLoadError(_MODEL_NAME, str(exc)) from exc

    def cleanup(self) -> None:
        """Release the model from memory."""
        self._model = None
        logger.info("model_cleaned_up", model_name=_MODEL_NAME)

    def predict(self, request: PredictionRequest) -> PredictionResult:
        """Run the forecasting inference."""
        self._ensure_loaded()

        history = self._extract_history(request)
        horizon = request.features.get("horizon", 24)

        try:
            point_forecast, quantile_forecast = self._model.forecast(
                horizon=horizon,
                inputs=[np.array(history, dtype=np.float32)],
            )

            # Extract scenarios from the 10 quantiles.
            scenarios = {
                "low_scenario": quantile_forecast[0, :, 1].tolist(),
                "most_likely": quantile_forecast[0, :, 5].tolist(),
                "high_scenario": quantile_forecast[0, :, 9].tolist(),
            }
        except Exception as exc:
            raise RuntimeError(f"TimesFM inference failed: {exc}") from exc

        return PredictionResult(
            model_name=_MODEL_NAME,
            model_version=_MODEL_VERSION,
            prediction={
                "horizon": horizon,
                "point_forecast": point_forecast[0].tolist(),
                "scenarios": scenarios,
            },
            confidence=1.0,
        )

    def input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "required": ["history"],
            "properties": {
                "history": {
                    "type": "array",
                    "items": {"type": "number"},
                    "description": "Historical time series values.",
                },
                "horizon": {
                    "type": "integer",
                    "description": "Number of steps to forecast.",
                    "default": 24,
                },
            },
        }

    def output_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "horizon": {"type": "integer"},
                "point_forecast": {
                    "type": "array",
                    "items": {"type": "number"},
                },
                "scenarios": {
                    "type": "object",
                    "properties": {
                        "low_scenario": {
                            "type": "array",
                            "items": {"type": "number"},
                        },
                        "most_likely": {
                            "type": "array",
                            "items": {"type": "number"},
                        },
                        "high_scenario": {
                            "type": "array",
                            "items": {"type": "number"},
                        },
                    },
                },
            },
        }

    def _ensure_loaded(self) -> None:
        if self._model is None:
            raise ModelLoadError(
                _MODEL_NAME,
                "Model is not loaded. Call load() before predict().",
            )

    @staticmethod
    def _extract_history(request: PredictionRequest) -> list[float]:
        history = request.features.get("history")
        if history is None:
            raise SchemaValidationError(
                _MODEL_NAME,
                ["Missing required feature: 'history'."],
            )
        if not isinstance(history, list):
            raise SchemaValidationError(
                _MODEL_NAME,
                [
                    f"Feature 'history' must be a list, got {type(history).__name__}."
                ],
            )
        return [float(x) for x in history]
