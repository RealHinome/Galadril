//! Galadril domain models.

use chrono::{DateTime, Utc};
use serde::Deserialize;

#[derive(Debug, Clone, Deserialize)]
pub struct PipelineConfig {
    pub name: String,
    pub connectors: ConnectorsConfig,
    #[serde(default)]
    pub sources: Vec<SourceConfig>,
}

#[derive(Debug, Clone, Deserialize)]
pub struct ConnectorsConfig {
    pub kafka: Option<KafkaConnectorConfig>,
    pub s3: Option<S3ConnectorConfig>,
}

#[derive(Debug, Clone, Deserialize)]
pub struct KafkaConnectorConfig {
    pub brokers: Vec<String>,
    pub schema_registry: String,
    pub consumer_group: String,
}

#[derive(Debug, Clone, Deserialize)]
pub struct S3ConnectorConfig {
    pub endpoint: String,
    pub access_key: String,
    pub secret_key: String,
    pub region: String,
    pub bucket_notifications: Option<String>,
}

#[derive(Debug, Clone, Deserialize)]
pub struct SourceConfig {
    pub id: String,
    pub topic: String,
    pub schema_path: Option<String>,
    pub match_pattern: Option<String>,
    #[serde(default = "default_parser")]
    pub parser: String,
}

fn default_parser() -> String {
    "metadata".to_string()
}

/// Abstraction of S3 notification.
#[derive(Debug, Clone)]
pub struct FileEvent {
    pub bucket: String,
    pub key: String,
    pub size: i64,
    pub received_at: DateTime<Utc>,
}
