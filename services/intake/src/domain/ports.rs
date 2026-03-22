//! Galadril ports.

use anyhow::Result;
use async_trait::async_trait;

// Driving Port for broker.
#[async_trait]
pub trait IngestionServicePort: Send + Sync {
    async fn process(&self, bucket: String, key: String) -> Result<()>;
}

// Driven Port for broker.
#[async_trait]
pub trait EventProducer: Send + Sync {
    /// Publish a dynamic payload.
    async fn publish(
        &self,
        topic: &str,
        schema_path: Option<&str>,
        key: &str,
        payload: &serde_json::Value,
    ) -> Result<()>;
}

// Driven Port for file storage.
#[async_trait]
pub trait BlobStorage: Send + Sync {
    async fn upload_file(
        &self,
        file_name: &str,
        data: &[u8],
    ) -> Result<String>;
    async fn download_file(&self, file_url: &str) -> Result<Vec<u8>>;
}
