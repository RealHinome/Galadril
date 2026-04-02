"""OpenAI Whisper model with optional Diarization."""

from __future__ import annotations

import os
from typing import Any

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

_MODEL_NAME = "whisper"
_MODEL_VERSION = "1.1.0"


class WhisperModel(BaseModel):
    """OpenAI Whisper optimized via Transformers pipeline + optional Pyannote."""

    def __init__(self) -> None:
        """Initialize the Whisper model wrapper."""
        self._pipe: Any | None = None
        self._diarization_pipe: Any | None = None
        self._device: str = "cpu"

    def meta(self) -> ModelMeta:
        """Return the immutable identity of this model."""
        return ModelMeta(
            name=_MODEL_NAME,
            version=_MODEL_VERSION,
            description="OpenAI Whisper model with optional Pyannote Diarization.",
            tags={
                "domain": "audio",
                "backend": "transformers+pyannote",
                "framework": "pytorch",
            },
        )

    def load(self, artifact_path: str) -> None:
        """Load the Whisper model and optionally the Pyannote pipeline."""
        try:
            import torch
            from transformers import pipeline
        except ImportError as exc:
            raise ModelLoadError(
                _MODEL_NAME,
                "transformers or torch is not installed.",
            ) from exc

        try:
            if torch.cuda.is_available():
                self._device = "cuda"
                dtype = torch.float16
                attn_impl = (
                    "flash_attention_2"
                    if torch.cuda.get_device_capability()[0] >= 8
                    else "sdpa"
                )
            elif torch.backends.mps.is_available():
                self._device = "mps"
                dtype = torch.float16
                attn_impl = "sdpa"
            else:
                self._device = "cpu"
                dtype = torch.float32
                attn_impl = "eager"

            self._pipe = pipeline(
                "automatic-speech-recognition",
                model=artifact_path,
                dtype=dtype,
                device=self._device,
                model_kwargs={"attn_implementation": attn_impl},
                ignore_warning=True,
            )

            local_diarization_config = os.path.join(
                artifact_path, "diarization", "config.yaml"
            )
            hf_token = os.environ.get("HF_TOKEN")

            if os.path.exists(local_diarization_config) or hf_token:
                try:
                    from pyannote.audio import Pipeline

                    if os.path.exists(local_diarization_config):
                        self._diarization_pipe = Pipeline.from_pretrained(
                            local_diarization_config
                        )
                    else:
                        self._diarization_pipe = Pipeline.from_pretrained(
                            "pyannote/speaker-diarization-3.1", token=hf_token
                        )

                    if self._diarization_pipe and self._device != "cpu":
                        self._diarization_pipe.to(torch.device(self._device))
                except ImportError:
                    logger.warning(
                        "pyannote.audio not installed, diarization disabled."
                    )
            else:
                logger.info(
                    "No HF_TOKEN or local config found. Diarization disabled."
                )

            logger.info(
                "model_loaded",
                model_name=_MODEL_NAME,
                device=self._device,
                dtype=str(dtype),
                attention=attn_impl,
                diarization_enabled=self._diarization_pipe is not None,
            )
        except Exception as exc:
            raise ModelLoadError(_MODEL_NAME, str(exc)) from exc

    def cleanup(self) -> None:
        """Release models and GPU memory."""
        self._pipe = None
        self._diarization_pipe = None
        import torch

        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        elif (
            hasattr(torch.backends, "mps") and torch.backends.mps.is_available()
        ):
            torch.mps.empty_cache()

        logger.info("model_cleaned_up", model_name=_MODEL_NAME)

    def predict(self, request: PredictionRequest) -> PredictionResult:
        """Run inference on the audio file, optionally with diarization."""
        self._ensure_loaded()

        audio = request.features.get("audio")
        if not audio or not isinstance(audio, str):
            raise SchemaValidationError(
                _MODEL_NAME,
                ["Feature 'audio' must be a valid file path string."],
            )

        enable_diarization = request.features.get("enable_diarization", False)
        if enable_diarization and not self._diarization_pipe:
            raise SchemaValidationError(
                _MODEL_NAME,
                ["Diarization requested but Pyannote pipeline is not loaded."],
            )

        task = request.features.get("task", "transcribe")
        language = request.features.get("language")

        generate_kwargs = {}
        if task != "transcribe":
            generate_kwargs["task"] = task
        if language:
            generate_kwargs["language"] = language

        inference_kwargs = {
            "chunk_length_s": 30,
            "batch_size": 24,
            "return_timestamps": True,
        }
        if generate_kwargs:
            inference_kwargs["generate_kwargs"] = generate_kwargs

        try:
            outputs = self._pipe(audio, **inference_kwargs)

            chunks = outputs.get("chunks", [])

            if enable_diarization:
                diarization = self._diarization_pipe(audio)
                chunks = self._align_diarization(chunks, diarization)

            return PredictionResult(
                model_name=_MODEL_NAME,
                model_version=_MODEL_VERSION,
                prediction={
                    "text": outputs.get("text", "").strip(),
                    "chunks": chunks,
                },
                confidence=1.0,
            )
        except Exception as exc:
            raise RuntimeError(f"Whisper inference failed: {exc}") from exc

    def _align_diarization(
        self, chunks: list[dict[str, Any]], diarization: Any
    ) -> list[dict[str, Any]]:
        """Align Whisper chunks with Pyannote speaker segments across versions."""
        aligned_chunks = []
        segments = []

        if hasattr(diarization, "itertracks"):
            for turn, _, spk in diarization.itertracks(yield_label=True):
                segments.append((turn.start, turn.end, spk))
        elif hasattr(diarization, "speaker_diarization"):
            for turn, spk in diarization.speaker_diarization:
                segments.append((turn.start, turn.end, spk))
        else:
            logger.warning(
                "Unsupported diarization output format. Skipping alignment."
            )
            return chunks

        for chunk in chunks:
            start, end = chunk["timestamp"]
            if end is None:
                end = start + 1.0

            midpoint = start + ((end - start) / 2)
            speaker = "UNKNOWN"

            for s_start, s_end, spk in segments:
                if s_start <= midpoint <= s_end:
                    speaker = spk
                    break

            chunk_data = chunk.copy()
            chunk_data["speaker"] = speaker
            aligned_chunks.append(chunk_data)

        return aligned_chunks

    def input_schema(self) -> dict[str, Any]:
        """Return a JSON Schema dict describing expected input features."""
        return {
            "type": "object",
            "required": ["audio"],
            "properties": {
                "audio": {"type": "string"},
                "task": {
                    "type": "string",
                    "enum": ["transcribe", "translate"],
                    "default": "transcribe",
                },
                "language": {"type": "string"},
                "enable_diarization": {"type": "boolean", "default": False},
            },
        }

    def output_schema(self) -> dict[str, Any]:
        """Return a JSON Schema dict describing the prediction output."""
        return {
            "type": "object",
            "properties": {
                "text": {"type": "string"},
                "chunks": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "timestamp": {
                                "type": "array",
                                "items": {"type": "number"},
                            },
                            "text": {"type": "string"},
                            "speaker": {"type": "string"},
                        },
                    },
                },
            },
        }

    def _ensure_loaded(self) -> None:
        """Ensure the base Whisper pipeline is loaded before prediction."""
        if self._pipe is None:
            raise ModelLoadError(_MODEL_NAME, "Model is not loaded.")
