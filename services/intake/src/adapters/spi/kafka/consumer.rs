//! Kafka consumer.

use std::sync::Arc;

use anyhow::{Context, Result, anyhow};
use rdkafka::Message;
use rdkafka::config::ClientConfig;
use rdkafka::consumer::{Consumer, StreamConsumer};
use serde::Deserialize;

use crate::domain::ports::IngestionServicePort;

/// MinIO/S3 notification.
///
/// [Reference](https://min.io/docs/minio/linux/administration/monitoring/bucket-notifications.html)
#[derive(Debug, Deserialize)]
#[serde(rename_all = "PascalCase")]
struct S3EventNotification {
    records: Vec<S3EventRecord>,
}

#[derive(Debug, Deserialize)]
#[serde(rename_all = "camelCase")]
struct S3EventRecord {
    event_name: String,
    s3: S3Entity,
}

#[derive(Debug, Deserialize)]
struct S3Entity {
    bucket: S3Bucket,
    object: S3Object,
}

#[derive(Debug, Deserialize)]
struct S3Bucket {
    name: String,
}

#[derive(Debug, Deserialize)]
#[serde(rename_all = "camelCase")]
struct S3Object {
    key: String,
    size: Option<i64>,
    e_tag: String,
    content_type: String,
}

pub struct KafkaConsumerAdapter {
    consumer: StreamConsumer,
    service: Arc<dyn IngestionServicePort>,
}

impl KafkaConsumerAdapter {
    /// Create a new [`KafkaConsumerAdapter`].
    pub fn new(
        brokers: &str,
        group_id: &str,
        topic: &str,
        service: Arc<dyn IngestionServicePort>,
    ) -> Result<Self> {
        let consumer: StreamConsumer = ClientConfig::new()
            .set("bootstrap.servers", brokers)
            .set("group.id", group_id)
            .set("auto.offset.reset", "earliest")
            .set("enable.auto.commit", "true")
            .create()?;

        consumer.subscribe(&[topic])?;

        Ok(Self { consumer, service })
    }

    /// Listening loop.
    pub async fn run(&self) -> Result<()> {
        loop {
            match self.consumer.recv().await {
                Ok(message) => {
                    let payload = message
                        .payload()
                        .ok_or_else(|| anyhow!("Empty message payload"))?;

                    if let Err(err) = self.handle_message(payload).await {
                        // TODO: send to DLQ.
                        eprintln!(
                            "Failed to process message at offset {}: {err:?}",
                            message.offset(),
                        );
                    }
                },
                Err(err) => {
                    eprintln!("Kafka consumer error: {err:?}");
                },
            }
        }
    }

    async fn handle_message(&self, payload: &[u8]) -> Result<()> {
        let notification: S3EventNotification =
            serde_json::from_slice(payload)
                .context("Failed to deserialize S3 event notification")?;

        for record in notification.records {
            if !record.event_name.starts_with("s3:ObjectCreated") {
                continue;
            }

            let bucket = record.s3.bucket.name;
            let key = record.s3.object.key;

            println!("New file detected: s3://{}/{}", bucket, key);

            self.service.process(bucket, key).await?;
        }

        Ok(())
    }
}
