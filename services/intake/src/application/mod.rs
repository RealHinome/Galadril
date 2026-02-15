//! Galadril application.

pub mod parsers;

use std::sync::Arc;

use anyhow::{Result, bail};
use async_trait::async_trait;
use chrono::Utc;

use crate::application::parsers::csv_financial::CsvFinancialParser;
use crate::application::parsers::json_osint::JsonOsintParser;
use crate::application::parsers::passthrough::PassthroughHandler;
use crate::domain::models::{DataSourceType, FileEvent};
use crate::domain::ports::{BlobStorage, EventProducer, IngestionServicePort};

pub struct IngestionService {
    storage: Arc<dyn BlobStorage>,
    producer: Arc<dyn EventProducer>,
}

impl IngestionService {
    /// Create a new [`IngestionService`].
    pub fn new(
        storage: Arc<dyn BlobStorage>,
        producer: Arc<dyn EventProducer>,
    ) -> Self {
        Self { storage, producer }
    }
}

#[async_trait]
impl IngestionServicePort for IngestionService {
    async fn process(&self, bucket: String, key: String) -> Result<()> {
        let event = FileEvent {
            bucket: bucket.clone(),
            key: key.clone(),
            size: 0,
            received_at: Utc::now(),
        };

        let source_type = event.infer_source_type();

        match source_type {
            DataSourceType::Financial => {
                let content = self.storage.download_file(&key).await?;
                CsvFinancialParser::parse_and_publish(
                    &content,
                    &self.producer,
                )
                .await?;
            },
            DataSourceType::Osint => {
                let content = self.storage.download_file(&key).await?;
                JsonOsintParser::parse_and_publish(&content, &self.producer)
                    .await?;
            },
            DataSourceType::Satellite => {
                PassthroughHandler::publish_satellite_meta(
                    &key,
                    &bucket,
                    &self.producer,
                )
                .await?;
            },

            DataSourceType::Document => {
                PassthroughHandler::publish_document_meta(
                    &key,
                    &bucket,
                    &self.producer,
                )
                .await?;
            },
            DataSourceType::Unknown => {
                bail!("unknown source type for key {key:?}");
            },
        }

        Ok(())
    }
}
