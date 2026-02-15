//! Custom configuration.

use std::env;

use anyhow::{Context, Result};

pub struct AppConfig {
    pub kafka_brokers: String,
    pub kafka_consumer_group: String,
    pub kafka_notification_topic: String,
    pub s3_endpoint: String,
    pub s3_bucket: String,
    pub topic: String,
}

impl AppConfig {
    pub fn from_env() -> Result<Self> {
        let _ = required("AWS_ACCESS_KEY_ID");
        let _ = required("AWS_SECRET_ACCESS_KEY");
        let _ = required("AWS_REGION");

        Ok(Self {
            kafka_brokers: required("KAFKA_BROKERS")?,
            kafka_consumer_group: optional(
                "KAFKA_CONSUMER_GROUP",
                "intake-service",
            ),
            kafka_notification_topic: optional(
                "KAFKA_TOPIC_NOTIFICATIONS",
                "s3-bucket-notifications",
            ),
            s3_endpoint: required("S3_ENDPOINT")?,
            s3_bucket: optional("S3_BUCKET", "my-bucket"),
            topic: optional("KAFKA_TOPIC", "raw"),
        })
    }
}

fn required(key: &str) -> Result<String> {
    env::var(key).context(format!("Missing required env var {key:?}"))
}

fn optional(key: &str, default: &str) -> String {
    env::var(key).unwrap_or_else(|_| default.to_string())
}
