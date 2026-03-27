"""Time series forecasting model powered by Google's TimesFM."""

from __future__ import annotations

from typing import Any, Literal, cast

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

_XRegMode = Literal["xreg + timesfm", "timesfm + xreg"]


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
        """Load the TimesFM model using the updated PyTorch API."""
        try:
            import timesfm  # type: ignore
            import torch  # type: ignore
        except ImportError as exc:
            raise ModelLoadError(
                _MODEL_NAME,
                "timesfm or torch is not installed. Install with: uv add timesfm torch",
            ) from exc

        try:
            torch.set_float32_matmul_precision("high")

            self._model = timesfm.TimesFM_2p5_200M_torch.from_pretrained(
                "google/timesfm-2.5-200m-pytorch"
            )

            self._model.compile(
                timesfm.ForecastConfig(
                    max_context=15000,
                    max_horizon=1000,
                    normalize_inputs=True,
                    use_continuous_quantile_head=True,
                    fix_quantile_crossing=True,
                    infer_is_positive=False,
                    return_backcast=False,
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
        """Run forecasting inference."""
        self._ensure_loaded()

        history = self._extract_history(request)
        horizon = self._extract_horizon(request)

        dyn_cov = request.features.get("dynamic_numerical_covariates")
        has_covariates = dyn_cov is not None and len(dyn_cov) > 0

        if hasattr(self._model, "config"):
            self._model.config.return_backcast = has_covariates

        try:
            inputs = [np.asarray(history, dtype=np.float32)]

            if not has_covariates:
                outputs = self._model.forecast(
                    horizon=horizon,
                    inputs=inputs,
                )
                point_forecast = outputs[0]
                quantile_forecast = outputs[1]
            else:
                dyn_num_cov = self._extract_dynamic_numerical_covariates(
                    request,
                    context_len=len(history),
                    horizon=horizon,
                )
                xreg_mode = self._extract_xreg_mode(request)

                ridge = request.features.get("ridge", 0.1)
                if not isinstance(ridge, (int, float)):
                    raise SchemaValidationError(
                        _MODEL_NAME,
                        [
                            f"Feature 'ridge' must be a number, got {type(ridge).__name__}."
                        ],
                    )

                model_outputs, xreg_outputs = (
                    self._model.forecast_with_covariates(
                        inputs=inputs,
                        dynamic_numerical_covariates=dyn_num_cov,
                        xreg_mode=xreg_mode,
                        ridge=float(ridge),
                    )
                )

                point_forecast = model_outputs[0]
                quantile_forecast = model_outputs[1]

            prediction_payload: dict[str, Any] = {
                "horizon": horizon,
                "point_forecast": point_forecast[0].tolist(),
                "quantiles": quantile_forecast[0].tolist(),
            }

            if has_covariates:
                prediction_payload["xreg_mode"] = self._extract_xreg_mode(
                    request
                )
                prediction_payload["xreg_outputs"] = xreg_outputs

            return PredictionResult(
                model_name=_MODEL_NAME,
                model_version=_MODEL_VERSION,
                prediction=prediction_payload,
                confidence=1.0,
            )

        except SchemaValidationError:
            raise
        except Exception as exc:
            raise RuntimeError(f"TimesFM inference failed: {exc}") from exc
        finally:
            if hasattr(self._model, "config"):
                self._model.config.return_backcast = False

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
                "dynamic_numerical_covariates": {
                    "type": "object",
                    "description": (
                        "Optional dict[str, list[float]] for a single series, "
                        "or dict[str, list[list[float]]] if extending to batching later. "
                        "Each covariate must be length (len(history) + horizon)."
                    ),
                    "additionalProperties": True,
                },
                "xreg_mode": {
                    "type": "string",
                    "enum": ["xreg + timesfm", "timesfm + xreg"],
                    "description": "How covariates are integrated when provided.",
                    "default": "xreg + timesfm",
                },
                "ridge": {
                    "type": "number",
                    "description": "Optional ridge regularization strength for xreg.",
                    "default": 0.1,
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
                "quantiles": {
                    "type": "array",
                    "description": "Raw quantile outputs. Shape: [horizon, 10] where index 0 is mean, 1-9 are deciles 0.1-0.9.",
                    "items": {"type": "array", "items": {"type": "number"}},
                },
                "xreg_mode": {"type": "string"},
                "xreg_outputs": {
                    "description": "Raw xreg outputs from TimesFM."
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
    def _extract_horizon(request: PredictionRequest) -> int:
        horizon = request.features.get("horizon", 24)
        if not isinstance(horizon, int):
            raise SchemaValidationError(
                _MODEL_NAME,
                [
                    f"Feature 'horizon' must be an int, got {type(horizon).__name__}."
                ],
            )
        if horizon <= 0:
            raise SchemaValidationError(
                _MODEL_NAME, ["Feature 'horizon' must be > 0."]
            )
        return horizon

    @staticmethod
    def _extract_history(request: PredictionRequest) -> list[float]:
        history = request.features.get("history")
        if history is None:
            raise SchemaValidationError(
                _MODEL_NAME, ["Missing required feature: 'history'."]
            )
        if not isinstance(history, list):
            raise SchemaValidationError(
                _MODEL_NAME,
                [
                    f"Feature 'history' must be a list, got {type(history).__name__}."
                ],
            )
        if not history:
            raise SchemaValidationError(
                _MODEL_NAME, ["Feature 'history' cannot be empty."]
            )
        return [float(x) for x in history]

    @staticmethod
    def _extract_xreg_mode(request: PredictionRequest) -> _XRegMode:
        raw = request.features.get("xreg_mode", "xreg + timesfm")
        if raw not in ("xreg + timesfm", "timesfm + xreg"):
            raise SchemaValidationError(
                _MODEL_NAME,
                [
                    "Feature 'xreg_mode' must be one of: "
                    "'xreg + timesfm', 'timesfm + xreg'."
                ],
            )
        return cast(_XRegMode, raw)

    @staticmethod
    def _extract_dynamic_numerical_covariates(
        request: PredictionRequest,
        *,
        context_len: int,
        horizon: int,
    ) -> dict[str, list[np.ndarray]]:
        raw = request.features.get("dynamic_numerical_covariates")
        if raw is None:
            return {}

        if not isinstance(raw, dict):
            raise SchemaValidationError(
                _MODEL_NAME,
                [
                    "Feature 'dynamic_numerical_covariates' must be a dict[str, list[float]]."
                ],
            )

        required_len = context_len + horizon
        parsed: dict[str, list[np.ndarray]] = {}

        for cov_name, cov_values in raw.items():
            if not isinstance(cov_name, str) or not cov_name:
                raise SchemaValidationError(
                    _MODEL_NAME,
                    ["Covariate names must be non-empty strings."],
                )

            if not isinstance(cov_values, list):
                raise SchemaValidationError(
                    _MODEL_NAME,
                    [
                        f"Covariate '{cov_name}' must be a list[float], "
                        f"got {type(cov_values).__name__}."
                    ],
                )

            if len(cov_values) != required_len:
                raise SchemaValidationError(
                    _MODEL_NAME,
                    [
                        f"Covariate '{cov_name}' length must be context_len + horizon "
                        f"({context_len} + {horizon} = {required_len}), got {len(cov_values)}."
                    ],
                )

            arr = np.asarray([float(x) for x in cov_values], dtype=np.float32)
            parsed[cov_name] = [arr]

        return parsed
