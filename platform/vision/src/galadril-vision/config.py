"""Configuration for galadril-vision."""

from __future__ import annotations

from pydantic import Field, PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class KafkaConfig(BaseSettings):
    """Kafka consumer configuration."""

    model_config = SettingsConfigDict(env_prefix="KAFKA_")

    bootstrap_servers: str = "localhost:9092"
    group_id: str = "galadril-vision"
    topic: str = "galadril.images.metadata"
    auto_offset_reset: str = "earliest"
    enable_auto_commit: bool = False
    max_poll_records: int = 100
    session_timeout_ms: int = 30000


class PostgresConfig(BaseSettings):
    """PostgreSQL connection configuration."""

    model_config = SettingsConfigDict(env_prefix="POSTGRES_")

    dsn: PostgresDsn = Field(
        default="postgresql://postgres:postgres@postgres:5432/galadril_dev"
    )
    min_connections: int = 5
    max_connections: int = 20

    graph_name: str = "galadril_social"

    # pgvectorscale settings.
    vector_dimensions: int = 512
    similarity_threshold: float = 0.85


class S3Config(BaseSettings):
    """S3 configuration for image storage."""

    model_config = SettingsConfigDict(env_prefix="S3_")

    bucket: str = "galadril-images"
    prefix: str = "raw"
    endpoint_url: str | None = None
    region_name: str = "eu-west-1"


class RayConfig(BaseSettings):
    """Ray cluster configuration."""

    model_config = SettingsConfigDict(env_prefix="RAY_")

    address: str | None = None  # None = local mode.
    num_cpus: int | None = None
    num_gpus: int | None = None


class VisionConfig(BaseSettings):
    """Root configuration aggregating all sub-configs."""

    model_config = SettingsConfigDict(
        env_prefix="VISION_",
        env_nested_delimiter="__",
    )

    kafka: KafkaConfig = Field(default_factory=KafkaConfig)
    postgres: PostgresConfig = Field(default_factory=PostgresConfig)
    s3: S3Config = Field(default_factory=S3Config)
    ray: RayConfig = Field(default_factory=RayConfig)

    # Pipeline settings.
    batch_size: int = 32
    inference_model: str = "face_recognition"
    unknown_vertex_prefix: str = "UNKNOWN"
