//! Galadril bronze layer for data ingestion.
#![deny(unsafe_code, missing_docs)]
#![allow(dead_code)]

mod adapters;
mod application;
mod domain;

use std::sync::Arc;

use tracing_subscriber::{EnvFilter, fmt, prelude::*};

use crate::adapters::spi::kafka::{
    KafkaConsumerAdapter, KafkaProducerAdapter,
};
use crate::adapters::spi::storage::S3Adapter;
use crate::application::IngestionService;
use crate::domain::config::AppConfig;

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    let level = if cfg!(debug_assertions) {
        "debug"
    } else {
        "info"
    };
    tracing_subscriber::registry()
        .with(
            EnvFilter::try_from_default_env()
                .unwrap_or_else(|_| EnvFilter::new(level)),
        )
        .with(fmt::layer())
        .init();

    let config = AppConfig::from_env()?;

    let s3_adapter = Arc::new(
        S3Adapter::new(&config.s3_endpoint, &config.s3_bucket).await?,
    );

    let kafka_producer = Arc::new(
        KafkaProducerAdapter::new(
            &config.kafka_brokers,
            &config.schema_registry,
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

    tracing::info!("galadril intake service ready");
    consumer.run().await
}
