//! Galadril bronze layer for data ingestion.
#![deny(unsafe_code, missing_docs)]
#![allow(dead_code)]

mod adapters;
mod application;
mod domain;

use std::sync::Arc;

use crate::{
    adapters::spi::{
        kafka::{KafkaConsumerAdapter, KafkaProducerAdapter},
        storage::S3Adapter,
    },
    application::IngestionService,
    domain::config::AppConfig,
};

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    let config = AppConfig::from_env()?;

    let s3_adapter = Arc::new(
        S3Adapter::new(&config.s3_endpoint, &config.s3_bucket).await?,
    );

    let kafka_producer = Arc::new(
        KafkaProducerAdapter::new(
            &config.kafka_brokers,
            &config.schema_registery,
            &config.topic,
        )
        .await?,
    );

    let ingestion_service =
        Arc::new(IngestionService::new(s3_adapter, kafka_producer));

    let consumer = KafkaConsumerAdapter::new(
        &config.kafka_brokers,
        &config.kafka_consumer_group,
        &config.kafka_notification_topic,
        ingestion_service,
    )?;

    println!("Galadril Intake Service starting...");
    consumer.run().await
}
