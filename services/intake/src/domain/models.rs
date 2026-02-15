//! Galadril domain models.

use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use std::collections::HashMap;

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize, Default)]
pub enum DataSourceType {
    #[default]
    Unknown,
    Financial,
    Satellite,
    Osint,
    Document,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DocumentMetadata {
    pub document_id: String,
    pub original_filename: String,
    pub storage_path: String,
    pub mime_type: String,
    pub file_hash: String,
    pub file_size_bytes: i64,
    pub ingested_at: DateTime<Utc>,
    pub source_context: Option<String>,
    #[serde(default)]
    pub metadata_tags: HashMap<String, String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FinancialTransaction {
    pub event_id: String,
    pub transaction_id: String,
    pub timestamp: DateTime<Utc>,
    pub sender_account: String,
    pub receiver_account: String,
    pub amount: f64,
    pub currency: String,
    pub transaction_type: Option<String>,
    pub source_system: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct OsintArticle {
    pub article_id: String,
    pub url: String,
    pub source_domain: String,
    pub published_at: Option<DateTime<Utc>>,
    pub collected_at: DateTime<Utc>,
    pub title: Option<String>,
    pub content_raw: String,
    pub author: Option<String>,
    pub language: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BoundingBox {
    pub top_left_lat: f64,
    pub top_left_lon: f64,
    pub bottom_right_lat: f64,
    pub bottom_right_lon: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SatelliteImageMetadata {
    pub image_id: String,
    pub storage_path: String,
    pub acquisition_date: DateTime<Utc>,
    pub provider: String,
    pub geometry: BoundingBox,
    pub resolution_meters: Option<f32>,
    pub cloud_cover_percentage: Option<f32>,
}

/// Abstraction of S3 notification.
pub struct FileEvent {
    pub bucket: String,
    pub key: String,
    pub size: i64,
    pub received_at: DateTime<Utc>,
}

impl FileEvent {
    /// Deduce the source type from the file path.
    pub fn infer_source_type(&self) -> DataSourceType {
        if self.key.contains("finance") {
            return DataSourceType::Financial;
        }
        if self.key.contains("satellite") {
            return DataSourceType::Satellite;
        }
        if self.key.contains("osint") || self.key.contains("news") {
            return DataSourceType::Osint;
        }
        if self.key.contains("doc") {
            return DataSourceType::Document;
        }

        DataSourceType::Unknown
    }
}
