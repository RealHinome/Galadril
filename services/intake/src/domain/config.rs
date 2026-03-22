//! Custom configuration merging Env and YAML.

use std::{env, fs};

use anyhow::{Context, Result};

use crate::domain::models::PipelineConfig;

pub struct AppConfig {
    pub kafka_brokers: String,
    pub kafka_consumer_group: String,
    pub kafka_notification_topic: String,
    pub schema_registry: String,
    pub s3_endpoint: String,
    pub s3_bucket: String,
    pub pipeline: PipelineConfig,
}

impl AppConfig {
    /// Load configuration from YAML and fallback to env vars.
    pub fn from_env() -> Result<Self> {
        tracing::debug!("reading configuration");

        let config_path = env::var("PIPELINE_PATH")
            .unwrap_or_else(|_| "pipeline.yaml".to_string());

        let file_content = fs::read_to_string(&config_path)?;
        let pipeline: PipelineConfig = serde_yaml::from_str(&file_content)?;

        let kafka_brokers = pipeline
            .connectors
            .kafka
            .as_ref()
            .map(|k| k.brokers.join(","))
            .or_else(|| env::var("KAFKA_BROKERS").ok())
            .context("Missing KAFKA_BROKERS")?;

        let schema_registry = pipeline
            .connectors
            .kafka
            .as_ref()
            .map(|k| k.schema_registry.clone())
            .or_else(|| env::var("SCHEMA_REGISTRY").ok())
            .context("Missing SCHEMA_REGISTRY")?;

        let kafka_consumer_group = pipeline
            .connectors
            .kafka
            .as_ref()
            .map(|k| k.consumer_group.clone())
            .unwrap_or_else(|| {
                env::var("KAFKA_CONSUMER_GROUP")
                    .unwrap_or_else(|_| "intake-service".to_string())
            });

        let s3_endpoint = pipeline
            .connectors
            .s3
            .as_ref()
            .map(|s| s.endpoint.clone())
            .or_else(|| env::var("S3_ENDPOINT").ok())
            .context("Missing S3_ENDPOINT")?;

        let kafka_notification_topic = pipeline
            .connectors
            .s3
            .as_ref()
            .and_then(|s| s.bucket_notifications.clone())
            .unwrap_or_else(|| {
                env::var("KAFKA_TOPIC_NOTIFICATIONS")
                    .unwrap_or_else(|_| "s3-bucket-notifications".to_string())
            });

        let s3_bucket =
            env::var("S3_BUCKET").unwrap_or_else(|_| "my-bucket".to_string());

        Ok(Self {
            kafka_brokers,
            kafka_consumer_group,
            kafka_notification_topic,
            schema_registry,
            s3_endpoint,
            s3_bucket,
            pipeline,
        })
    }
}
