from __future__ import annotations

from typing import Any, Literal
from pydantic import BaseModel, Field, HttpUrl


class KafkaConnectorConfig(BaseModel):
    brokers: list[str]
    schema_registry: HttpUrl | str
    consumer_group: str


class S3ConnectorConfig(BaseModel):
    endpoint: HttpUrl | str
    access_key: str
    secret_key: str
    region: str
    bucket_notifications: str | None = None


class PostgresConnectorConfig(BaseModel):
    database: str
    host: str
    user: str
    password: str


class ConnectorsConfig(BaseModel):
    kafka: KafkaConnectorConfig
    s3: S3ConnectorConfig | None = None
    postgres: PostgresConnectorConfig | None = None


class SourceConfig(BaseModel):
    id: str
    topic: str
    schema_path: str


class DuckDBAggregateConfig(BaseModel):
    enabled: bool = False
    query: str | None = None


class PipelineStepConfig(BaseModel):
    step: str
    type: Literal["inference", "transform", "sink"] = "inference"
    model: str
    artifact_path: str | None = None
    input_from: list[str] = Field(default_factory=list)
    params: dict[str, Any] = Field(default_factory=dict)
    duckdb: DuckDBAggregateConfig | None = None


class PipelineYamlConfig(BaseModel):
    name: str
    connectors: ConnectorsConfig
    sources: list[SourceConfig]
    pipeline: list[PipelineStepConfig]
