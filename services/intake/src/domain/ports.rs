//! Galadril ports.

use anyhow::Result;
use async_trait::async_trait;

use crate::domain::models::{
    DocumentMetadata, FinancialTransaction, OsintArticle,
    SatelliteImageMetadata,
};

// Driving Port for broker.
#[async_trait]
pub trait IngestionServicePort: Send + Sync {
    // Orchestrator.
    async fn process(&self, bucket: String, key: String) -> Result<()>;
}

// Driven Port for broker.
#[async_trait]
pub trait EventProducer: Send + Sync {
    async fn publish_financial(
        &self,
        event: FinancialTransaction,
    ) -> Result<()>;
    async fn publish_satellite_meta(
        &self,
        meta: SatelliteImageMetadata,
    ) -> Result<()>;
    async fn publish_document(&self, doc: DocumentMetadata) -> Result<()>;
    async fn publish_osint(&self, article: OsintArticle) -> Result<()>;
}

// Driven Port for file storage.
#[async_trait]
pub trait BlobStorage: Send + Sync {
    /// Upload a new file on object storage.
    async fn upload_file(&self, file_name: &str, data: &[u8]) -> Result<&str>;
    /// Get data of a file on object storage.
    async fn download_file(&self, file_url: &str) -> Result<&[u8]>;
}
