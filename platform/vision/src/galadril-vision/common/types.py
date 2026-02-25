"""Shared types for galadril-vision."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum, unique
from typing import Any
from uuid import uuid4


def _generate_id() -> str:
    return uuid4().hex


@unique
class ProcessingStatus(StrEnum):
    """Status of image processing in the pipeline."""

    PENDING = "pending"
    DOWNLOADED = "downloaded"
    PROCESSED = "processed"
    IDENTIFIED = "identified"
    STORED = "stored"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class ImageMetadata:
    """Metadata received from Kafka (enriched by Spark)."""

    image_id: str
    storage_path: str  # S3 path to the image
    source: str
    captured_at: datetime
    enrichments: dict[str, Any] = field(default_factory=dict)

    content_type: str = "image/jpeg"
    file_size_bytes: int = 0
    checksum: str = ""


@dataclass(slots=True)
class DetectedFaceRecord:
    """A face detected in an image with identification status."""

    face_id: str = field(default_factory=_generate_id)
    image_id: str = ""
    bbox: list[float] = field(default_factory=list)
    confidence: float = 0.0
    embedding: list[float] = field(default_factory=list)

    identified_person_id: str | None = None
    identification_confidence: float = 0.0
    is_unknown: bool = True


@dataclass(slots=True)
class ProcessedImage:
    """Result of processing a single image through the pipeline."""

    image_id: str
    metadata: ImageMetadata
    status: ProcessingStatus = ProcessingStatus.PENDING
    faces: list[DetectedFaceRecord] = field(default_factory=list)
    processing_time_ms: float = 0.0
    error: str | None = None


@dataclass(frozen=True, slots=True)
class GraphEdge:
    """An edge to create in Apache AGE between two persons."""

    source_vertex_id: str
    target_vertex_id: str
    edge_type: str  # e.g., "APPEARS_WITH", "SAME_IMAGE".
    properties: dict[str, Any] = field(default_factory=dict)
