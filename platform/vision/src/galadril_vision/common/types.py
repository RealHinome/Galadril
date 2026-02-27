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
    """Status of record processing in the pipeline."""

    PENDING = "pending"
    DOWNLOADED = "downloaded"
    PROCESSED = "processed"
    IDENTIFIED = "identified"
    STORED = "stored"
    SKIPPED = "skipped"
    FAILED = "failed"


@unique
class EntityType(StrEnum):
    """Types of entities that can be extracted and linked in the graph."""

    PERSON = "Person"
    ORGANIZATION = "Organization"
    LOCATION = "Location"
    ACCOUNT = "Account"  # Financial account.
    DOCUMENT = "Document"
    VEHICLE = "Vehicle"
    BUILDING = "Building"
    UNKNOWN = "Unknown"


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
class ExtractedEntity:
    """An entity extracted from any input type."""

    entity_id: str = field(default_factory=_generate_id)
    entity_type: EntityType = EntityType.UNKNOWN
    source_record_id: str = ""  # Links back to the input record.

    name: str | None = None
    embedding: list[float] = field(default_factory=list)
    properties: dict[str, Any] = field(default_factory=dict)

    resolved_id: str | None = None  # Linked to known entity in graph.
    resolution_confidence: float = 0.0
    is_resolved: bool = False


@dataclass(slots=True)
class ProcessedRecord:
    """Result of processing any input type through the pipeline."""

    record_id: str
    input_type: str
    status: ProcessingStatus = ProcessingStatus.PENDING

    faces: list[DetectedFaceRecord] = field(default_factory=list)
    entities: list[ExtractedEntity] = field(default_factory=list)

    processing_time_ms: float = 0.0
    error: str | None = None
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass(frozen=True, slots=True)
class GraphVertex:
    """A vertex to create/update in Apache AGE."""

    vertex_id: str
    label: EntityType
    properties: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class GraphEdge:
    """An edge to create in Apache AGE between two entities."""

    source_vertex_id: str
    target_vertex_id: str
    edge_type: str
    properties: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class DetectedObject:
    """An object detected in satellite imagery."""

    object_id: str = field(default_factory=_generate_id)
    image_id: str = ""
    object_type: str = ""
    bbox: list[float] = field(default_factory=list)
    geo_coords: list[float] = field(default_factory=list)
    confidence: float = 0.0
    properties: dict[str, Any] = field(default_factory=dict)
