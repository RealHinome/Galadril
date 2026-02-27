"""Kafka message schemas."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum, unique

from pydantic import BaseModel, Field


@unique
class InputType(StrEnum):
    """Supported input types for the vision pipeline."""

    SATELLITE_IMAGE = "satellite_image"
    DOCUMENT = "document"
    OSINT_ARTICLE = "osint_article"
    FINANCIAL_TRANSACTION = "financial_transaction"


class BoundingBox(BaseModel):
    """Geospatial bounding box."""

    top_left_lat: float
    top_left_lon: float
    bottom_right_lat: float
    bottom_right_lon: float


class SatelliteImageMessage(BaseModel):
    """Schema for satellite image metadata from Kafka.

    Aligned with: schemas/avro/satellite.avsc
    """

    image_id: str = Field(
        ..., description="Unique identifier for the image asset."
    )
    storage_path: str = Field(
        ..., description="S3/MinIO URI where the GeoTIFF/image is stored."
    )
    acquisition_date: datetime = Field(
        ..., description="When the image was acquired."
    )
    provider: str = Field(..., description="e.g., ESA_Sentinel, Maxar, Planet.")
    geometry: BoundingBox = Field(
        ..., description="Geospatial coverage of the image."
    )
    resolution_meters: float | None = Field(
        default=None, description="Pixel resolution in meters."
    )
    cloud_cover_percentage: float | None = Field(default=None)

    def to_input_type(self) -> InputType:
        return InputType.SATELLITE_IMAGE


class DocumentMessage(BaseModel):
    """Schema for document metadata from Kafka.

    Aligned with: schemas/avro/document.avsc
    """

    document_id: str = Field(..., description="Internal UUID.")
    original_filename: str
    storage_path: str = Field(
        ..., description="S3/MinIO path where the binary file is stored."
    )
    mime_type: str = Field(
        ..., description="e.g., 'application/pdf', 'image/jpeg'."
    )
    file_hash: str = Field(..., description="SHA-256 hash for deduplication.")
    file_size_bytes: int
    ingested_at: datetime
    source_context: str | None = Field(
        default=None,
        description="e.g., 'Leaked Panama Papers', 'Internal Audit 2024'.",
    )
    metadata_tags: dict[str, str] = Field(default_factory=dict)

    def to_input_type(self) -> InputType:
        return InputType.DOCUMENT


class OsintArticleMessage(BaseModel):
    """Schema for OSINT article metadata from Kafka.

    Aligned with: schemas/avro/osint.avsc
    """

    article_id: str
    url: str = Field(..., description="Source URL of the content.")
    source_domain: str = Field(
        ..., description="e.g., 'reuters.com', 'twitter.com'."
    )
    published_at: datetime | None = Field(default=None)
    collected_at: datetime
    title: str | None = Field(default=None)
    content_raw: str = Field(..., description="Full text content or HTML body.")
    author: str | None = Field(default=None)
    language: str | None = Field(
        default=None, description="ISO 639-1 language code."
    )

    def to_input_type(self) -> InputType:
        return InputType.OSINT_ARTICLE


class FinancialTransactionMessage(BaseModel):
    """Schema for financial transaction from Kafka.

    Aligned with: schemas/avro/finance.avsc
    """

    event_id: str = Field(
        ..., description="Unique UUID for this event in Galadril."
    )
    transaction_id: str = Field(..., description="ID from the source system.")
    timestamp: datetime = Field(
        ..., description="Time when the transaction occurred."
    )
    sender_account: str
    receiver_account: str
    amount: float
    currency: str = Field(
        ..., description="ISO 4217 currency code (e.g., USD, EUR, BTC)."
    )
    transaction_type: str | None = Field(
        default=None,
        description="e.g., TRANSFER, WITHDRAWAL, DEPOSIT.",
    )
    source_system: str = Field(..., description="Name of the bank or exchange.")

    def to_input_type(self) -> InputType:
        return InputType.FINANCIAL_TRANSACTION


class UnifiedInputRecord(BaseModel):
    """Unified wrapper for all input types in the pipeline."""

    input_type: InputType
    record_id: str = Field(..., description="Unique ID across all input types.")
    storage_path: str | None = Field(
        default=None,
        description="S3 path for binary content (images, documents).",
    )
    timestamp: datetime = Field(
        ..., description="Event or acquisition timestamp."
    )
    source: str = Field(..., description="Origin of the data.")

    satellite: SatelliteImageMessage | None = None
    document: DocumentMessage | None = None
    osint: OsintArticleMessage | None = None
    financial: FinancialTransactionMessage | None = None

    @classmethod
    def from_satellite(cls, msg: SatelliteImageMessage) -> "UnifiedInputRecord":
        return cls(
            input_type=InputType.SATELLITE_IMAGE,
            record_id=msg.image_id,
            storage_path=msg.storage_path,
            timestamp=msg.acquisition_date,
            source=msg.provider,
            satellite=msg,
        )

    @classmethod
    def from_document(cls, msg: DocumentMessage) -> "UnifiedInputRecord":
        return cls(
            input_type=InputType.DOCUMENT,
            record_id=msg.document_id,
            storage_path=msg.storage_path,
            timestamp=msg.ingested_at,
            source=msg.source_context or "unknown",
            document=msg,
        )

    @classmethod
    def from_osint(cls, msg: OsintArticleMessage) -> "UnifiedInputRecord":
        return cls(
            input_type=InputType.OSINT_ARTICLE,
            record_id=msg.article_id,
            storage_path=None,
            timestamp=msg.collected_at,
            source=msg.source_domain,
            osint=msg,
        )

    @classmethod
    def from_financial(
        cls, msg: FinancialTransactionMessage
    ) -> "UnifiedInputRecord":
        return cls(
            input_type=InputType.FINANCIAL_TRANSACTION,
            record_id=msg.event_id,
            storage_path=None,
            timestamp=msg.timestamp,
            source=msg.source_system,
            financial=msg,
        )

    @property
    def has_binary_content(self) -> bool:
        """Check if this record has associated binary content to download."""
        return self.storage_path is not None

    @property
    def is_image(self) -> bool:
        """Check if this record contains image data."""
        if self.input_type == InputType.SATELLITE_IMAGE:
            return True
        if self.input_type == InputType.DOCUMENT and self.document:
            return self.document.mime_type.startswith("image/")
        return False
