use std::sync::Arc;

use anyhow::Result;
use chrono::Utc;
use uuid::Uuid;

use crate::domain::models::{
    BoundingBox, DocumentMetadata, SatelliteImageMetadata,
};
use crate::domain::ports::EventProducer;

pub struct PassthroughHandler;

impl PassthroughHandler {
    pub async fn publish_satellite_meta(
        key: &str,
        bucket: &str,
        producer: &Arc<dyn EventProducer>,
    ) -> Result<()> {
        let meta = SatelliteImageMetadata {
            image_id: Uuid::new_v4().to_string(),
            storage_path: format!("s3://{}/{}", bucket, key),
            acquisition_date: Utc::now(),
            provider: extract_provider_from_key(key),
            geometry: BoundingBox {
                top_left_lat: 0.0,
                top_left_lon: 0.0,
                bottom_right_lat: 0.0,
                bottom_right_lon: 0.0,
            },
            resolution_meters: None,
            cloud_cover_percentage: None,
        };

        producer.publish_satellite_meta(meta).await
    }

    pub async fn publish_document_meta(
        key: &str,
        bucket: &str,
        producer: &Arc<dyn EventProducer>,
    ) -> Result<()> {
        let doc = DocumentMetadata {
            document_id: Uuid::new_v4().to_string(),
            original_filename: key
                .rsplit('/')
                .next()
                .unwrap_or(key)
                .to_string(),
            storage_path: format!("s3://{}/{}", bucket, key),
            mime_type: infer_mime_type(key),
            file_hash: String::new(),
            file_size_bytes: 0,
            ingested_at: Utc::now(),
            source_context: None,
            metadata_tags: Default::default(),
        };

        producer.publish_document(doc).await
    }
}

/// Deducts the satellite provider from the S3 path.
fn extract_provider_from_key(key: &str) -> String {
    key.split('/').nth(1).unwrap_or("unknown").to_string()
}

/// Deducts the MIME type from the file extension.
///
/// TODO: use Google Magika instead of heuristic.
fn infer_mime_type(key: &str) -> String {
    match key.rsplit('.').next() {
        Some("pdf") => "application/pdf",
        Some("csv") => "text/csv",
        Some("json") => "application/json",
        Some("tiff") | Some("tif") => "image/tiff",
        Some("jpg") | Some("jpeg") => "image/jpeg",
        Some("png") => "image/png",
        _ => "application/octet-stream",
    }
    .to_string()
}
