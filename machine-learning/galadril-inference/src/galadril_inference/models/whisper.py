"""OpenAI Whisper model with optional Diarization and Speaker Embeddings."""

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
_MODEL_VERSION = "1.2.0"


class WhisperModel(BaseModel):
    """OpenAI Whisper pipeline with optional Pyannote and embeddings."""

    def __init__(self) -> None:
        """Initialize the Whisper model wrapper."""
        self._pipe: Any | None = None
        self._diarization_pipe: Any | None = None
        self._embedding_inference: Any | None = None
        self._device: str = "cpu"

    def meta(self) -> ModelMeta:
        """Return the immutable identity of this model."""
        return ModelMeta(
            name=_MODEL_NAME,
            version=_MODEL_VERSION,
            description="OpenAI Whisper model with optional Pyannote Diarization and Embeddings.",
            tags={
                "domain": "audio",
                "backend": "transformers+pyannote",
                "framework": "pytorch",
            },
        )

    def load(self, artifact_path: str) -> None:
        """Load the Whisper model and optionally the Pyannote pipelines."""
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
                    from pyannote.audio import Pipeline, Model, Inference

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

                    try:
                        emb_model = Model.from_pretrained(
                            "pyannote/wespeaker-voxceleb-resnet34-LM",
                            token=hf_token,
                        )
                        self._embedding_inference = Inference(
                            emb_model,
                            window="whole",
                            device=torch.device(self._device),
                        )
                    except Exception as emb_exc:
                        logger.warning(
                            f"Could not load embedding model: {emb_exc}"
                        )

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
                embeddings_enabled=self._embedding_inference is not None,
            )
        except Exception as exc:
            raise ModelLoadError(_MODEL_NAME, str(exc)) from exc

    def cleanup(self) -> None:
        """Release models and GPU memory."""
        self._pipe = None
        self._diarization_pipe = None
        self._embedding_inference = None
        import torch

        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        elif (
            hasattr(torch.backends, "mps") and torch.backends.mps.is_available()
        ):
            torch.mps.empty_cache()

        logger.info("model_cleaned_up", model_name=_MODEL_NAME)

    def predict(self, request: PredictionRequest) -> PredictionResult:
        """Run inference on the audio file, optionally with diarization and embeddings."""
        self._ensure_loaded()

        audio = request.features.get("audio")
        if not audio or not isinstance(audio, str):
            raise SchemaValidationError(
                _MODEL_NAME,
                ["Feature 'audio' must be a valid file path string."],
            )

        enable_diarization = request.features.get("enable_diarization", False)
        enable_embeddings = request.features.get("enable_embeddings", False)

        if enable_diarization and not self._diarization_pipe:
            raise SchemaValidationError(
                _MODEL_NAME,
                ["Diarization requested but Pyannote pipeline is not loaded."],
            )

        if enable_embeddings and not self._embedding_inference:
            raise SchemaValidationError(
                _MODEL_NAME,
                ["Embeddings requested but wespeaker model is not loaded."],
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
            "batch_size": 1,
            "return_timestamps": True,
        }
        if generate_kwargs:
            inference_kwargs["generate_kwargs"] = generate_kwargs

        try:
            outputs = self._pipe(audio, **inference_kwargs)
            chunks = outputs.get("chunks", [])

            if enable_diarization:
                import torchaudio

                waveform, sample_rate = torchaudio.load(audio)

                if waveform.shape[0] > 1:
                    waveform = waveform.mean(dim=0, keepdim=True)

                audio_in_memory = {
                    "waveform": waveform,
                    "sample_rate": sample_rate,
                }

                diarization = self._diarization_pipe(audio_in_memory)
                chunks = self._align_diarization(
                    chunks,
                    diarization,
                    audio_path=audio_in_memory if enable_embeddings else None,
                )

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
        self,
        chunks: list[dict[str, Any]],
        diarization: Any,
        audio_path: str | dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Align Whisper chunks with Pyannote speaker segments and extract embeddings."""
        from pyannote.core import Segment

        audio_duration = float("inf")
        if audio_path is not None:
            try:
                if isinstance(audio_path, dict):
                    audio_duration = (
                        audio_path["waveform"].shape[1]
                        / audio_path["sample_rate"]
                    )
                else:
                    import torchaudio

                    info = torchaudio.info(audio_path)
                    audio_duration = info.num_frames / info.sample_rate
            except Exception as e:
                logger.warning(f"Could not read audio duration: {e}")

        aligned_chunks = []
        segments = []

        if hasattr(diarization, "itertracks"):
            for turn, _, spk in diarization.itertracks(yield_label=True):
                segments.append((turn, spk))
        elif hasattr(diarization, "speaker_diarization"):
            for turn, spk in diarization.speaker_diarization:
                segments.append((turn, spk))
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
            matched_segment = None

            for turn, spk in segments:
                if turn.start <= midpoint <= turn.end:
                    speaker = spk
                    matched_segment = turn
                    break

            chunk_data = {
                "timestamp": chunk["timestamp"],
                "text": chunk["text"],
                "speaker": speaker,
            }

            if audio_path and self._embedding_inference:
                try:
                    if matched_segment:
                        embedding = self._embedding_inference.crop(
                            audio_path, matched_segment
                        )
                    else:
                        safe_end = min(end, audio_duration)
                        if start >= safe_end:
                            safe_end = start + 0.1

                        whisper_segment = Segment(start, safe_end)
                        embedding = self._embedding_inference.crop(
                            audio_path, whisper_segment
                        )

                    if hasattr(embedding, "tolist"):
                        chunk_data["speaker_embedding"] = embedding.tolist()
                    else:
                        chunk_data["speaker_embedding"] = None

                except Exception as e:
                    logger.warning(
                        f"Failed to extract embedding for chunk: {e}"
                    )
                    chunk_data["speaker_embedding"] = None
            else:
                chunk_data["speaker_embedding"] = None

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
                "enable_embeddings": {"type": "boolean", "default": False},
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
                            "speaker_embedding": {
                                "type": ["array", "null"],
                                "items": {"type": "number"},
                                "description": "Speaker voice embedding vector if enabled",
                            },
                        },
                    },
                },
            },
        }

    def _ensure_loaded(self) -> None:
        """Ensure the base Whisper pipeline is loaded before prediction."""
        if self._pipe is None:
            raise ModelLoadError(_MODEL_NAME, "Model is not loaded.")
