"""OpenAI Whisper model with optional Diarization and Speaker Embeddings."""

from __future__ import annotations

import os
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

_MODEL_NAME = "whisper"
_MODEL_VERSION = "1.1.0"


class WhisperModel(BaseModel):
    """Whisper pipeline using faster-whisper, ONNX segmentation, and wespeakerruntime."""

    def __init__(self) -> None:
        """Initialize the Whisper model wrapper."""
        self._pipe: Any | None = None
        self._segmentation_session: Any | None = None
        self._embedding_inference: Any | None = None

    def meta(self) -> ModelMeta:
        """Return the immutable identity of this model."""
        return ModelMeta(
            name=_MODEL_NAME,
            version=_MODEL_VERSION,
            description="Whisper model with Pyannote Segmentation (ONNX) and WeSpeaker Embeddings.",
            tags={
                "domain": "audio",
                "backend": "faster-whisper+onnx+wespeaker",
                "framework": "numpy",
            },
        )

    def load(self, artifact_path: str, compute_type: str = "default") -> None:
        """Load the faster-whisper model and ONNX pipelines. Downloads them to artifact_path if missing."""
        try:
            from faster_whisper import WhisperModel as FasterWhisper
            from huggingface_hub import hf_hub_download
        except ImportError as exc:
            raise ModelLoadError(
                _MODEL_NAME,
                "faster-whisper or huggingface_hub is not installed.",
            ) from exc

        try:
            os.makedirs(artifact_path, exist_ok=True)

            if compute_type in ["float16", "fp16"]:
                seg_file_target = "onnx/model_fp16.onnx"
            elif compute_type == "int8":
                seg_file_target = "onnx/model_int8.onnx"
            else:
                seg_file_target = "onnx/model.onnx"

            whisper_dir = os.path.join(artifact_path, "whisper")
            os.makedirs(whisper_dir, exist_ok=True)

            self._pipe = FasterWhisper(
                model_size_or_path="base",
                device="auto",
                compute_type=compute_type,
                download_root=whisper_dir,
            )

            diarization_dir = os.path.join(artifact_path, "diarization")
            os.makedirs(diarization_dir, exist_ok=True)

            def safe_download(repo, target_file, fallback_file):
                """Download model."""
                try:
                    return hf_hub_download(
                        repo_id=repo,
                        filename=target_file,
                        local_dir=diarization_dir,
                    )
                except Exception as e:
                    logger.info(
                        f"File {target_file} not found in {repo}, falling back to {fallback_file}..."
                    )
                    return hf_hub_download(
                        repo_id=repo,
                        filename=fallback_file,
                        local_dir=diarization_dir,
                    )

            seg_model_path = safe_download(
                "onnx-community/pyannote-segmentation-3.0",
                seg_file_target,
                "onnx/model.onnx",
            )

            if os.path.exists(seg_model_path):
                try:
                    import onnxruntime as ort
                    import wespeakerruntime as wespeaker

                    self._segmentation_session = ort.InferenceSession(
                        seg_model_path,
                        providers=[
                            "CUDAExecutionProvider",
                            "CoreMLExecutionProvider",
                            "CPUExecutionProvider",
                        ],
                    )
                    self._embedding_inference = wespeaker.Speaker(lang="en")

                except ImportError:
                    logger.warning(
                        "onnxruntime or wespeakerruntime not installed, diarization disabled."
                    )
            else:
                logger.warning("ONNX files missing. Diarization disabled.")

            logger.info(
                "model_loaded",
                model_name=_MODEL_NAME,
                backend="faster-whisper",
                diarization_enabled=self._segmentation_session is not None,
                embeddings_enabled=self._embedding_inference is not None,
            )
        except Exception as exc:
            raise ModelLoadError(_MODEL_NAME, str(exc)) from exc

    def cleanup(self) -> None:
        """Release models and memory."""
        self._pipe = None
        self._segmentation_session = None
        self._embedding_inference = None
        logger.info("model_cleaned_up", model_name=_MODEL_NAME)

    def predict(self, request: PredictionRequest) -> PredictionResult:
        """Run inference on the raw audio waveform."""
        self._ensure_loaded()

        audio_data = request.features.get("audio")
        if (
            not audio_data
            or not isinstance(audio_data, dict)
            or "waveform" not in audio_data
        ):
            raise SchemaValidationError(
                _MODEL_NAME,
                [
                    "Feature 'audio' must be a dict containing 'waveform' (NumPy array) and 'sample_rate' (int)."
                ],
            )

        raw_waveform = audio_data["waveform"]
        orig_sr = audio_data.get("sample_rate", 16000)

        enable_diarization = request.features.get("enable_diarization", False)
        task = request.features.get("task", "transcribe")
        language = request.features.get("language")

        try:
            import librosa

            if len(raw_waveform.shape) > 1:
                raw_waveform = raw_waveform.mean(axis=1)

            if orig_sr != 16000:
                waveform_16k = librosa.resample(
                    y=raw_waveform, orig_sr=orig_sr, target_sr=16000
                )
            else:
                waveform_16k = raw_waveform

            waveform_16k = waveform_16k.astype(np.float32)

            segments_gen, info = self._pipe.transcribe(
                waveform_16k, task=task, language=language, vad_filter=True
            )

            chunks = []
            full_text = ""
            for segment in segments_gen:
                chunks.append(
                    {
                        "timestamp": [segment.start, segment.end],
                        "text": segment.text,
                    }
                )
                full_text += segment.text + " "

            full_text = full_text.strip()

            if enable_diarization and chunks:
                chunks = self._align_diarization(chunks, waveform=waveform_16k)

            return PredictionResult(
                model_name=_MODEL_NAME,
                model_version=_MODEL_VERSION,
                prediction={
                    "text": full_text,
                    "chunks": chunks,
                    "language": info.language
                    if hasattr(info, "language")
                    else language,
                },
                confidence=1.0,
            )
        except Exception as exc:
            raise RuntimeError(f"Whisper inference failed: {exc}") from exc

    def _align_diarization(
        self, chunks: list[dict[str, Any]], waveform: np.ndarray
    ) -> list[dict[str, Any]]:
        """Align Whisper chunks using Agglomerative Clustering (Pyannote style)."""
        import io
        import scipy.io.wavfile as wavfile
        from sklearn.cluster import AgglomerativeClustering
        from sklearn.neighbors import kneighbors_graph

        sr = 16000
        aligned_chunks = []
        valid_embeddings = []
        chunk_indices = []

        for i, chunk in enumerate(chunks):
            start, end = chunk["timestamp"]
            if end is None:
                end = start + 1.0

            start_sample = int(start * sr)
            end_sample = int(end * sr)
            chunk_waveform = waveform[start_sample:end_sample]

            if (
                len(chunk_waveform) > int(0.6 * sr)
                and self._embedding_inference
            ):
                wav_buffer = io.BytesIO()
                wavfile.write(wav_buffer, sr, chunk_waveform)
                wav_buffer.seek(0)

                try:
                    emb = self._embedding_inference.extract_embedding(
                        wav_buffer
                    )

                    if isinstance(emb, list):
                        emb = np.array(emb)

                    emb = emb.flatten()
                    emb = emb / (np.linalg.norm(emb) + 1e-8)

                    valid_embeddings.append(emb)
                    chunk_indices.append(i)
                except Exception as e:
                    logger.warning(
                        f"Failed to extract embedding from memory buffer: {e}"
                    )

        speaker_assignments = ["UNKNOWN"] * len(chunks)

        if len(valid_embeddings) > 0:
            X = np.array(valid_embeddings)
            connectivity = kneighbors_graph(
                X, n_neighbors=2, include_self=False
            )

            DISTANCE_THRESHOLD = 0.7

            clusterer = AgglomerativeClustering(
                n_clusters=None,
                metric="cosine",
                linkage="average",
                distance_threshold=DISTANCE_THRESHOLD,
                connectivity=connectivity,
            )

            labels = clusterer.fit_predict(X)

            for emb_idx, chunk_idx in enumerate(chunk_indices):
                speaker_assignments[chunk_idx] = (
                    f"SPEAKER_{labels[emb_idx] + 1:02d}"
                )

        last_known_speaker = "UNKNOWN"
        for i in range(len(chunks)):
            if (
                speaker_assignments[i] == "UNKNOWN"
                and last_known_speaker != "UNKNOWN"
            ):
                speaker_assignments[i] = last_known_speaker
            elif speaker_assignments[i] != "UNKNOWN":
                last_known_speaker = speaker_assignments[i]

        for i, chunk in enumerate(chunks):
            chunk_data = {
                "timestamp": chunk["timestamp"],
                "text": chunk["text"],
                "speaker": speaker_assignments[i],
                "speaker_embedding": None,
            }
            aligned_chunks.append(chunk_data)

        return aligned_chunks

    def input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "required": ["audio"],
            "properties": {
                "audio": {
                    "type": "object",
                    "properties": {
                        "waveform": {
                            "description": "NumPy ndarray of the audio"
                        },
                        "sample_rate": {"type": "integer"},
                    },
                },
                "task": {"type": "string"},
                "language": {"type": "string"},
                "enable_diarization": {"type": "boolean", "default": False},
            },
        }

    def output_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "text": {"type": "string"},
                "chunks": {"type": "array"},
            },
        }

    def _ensure_loaded(self) -> None:
        if self._pipe is None:
            raise ModelLoadError(_MODEL_NAME, "Model is not loaded.")
