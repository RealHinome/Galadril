//! Outbound port for database inspection.

use anyhow::Result;
use serde_json::Value;

use crate::domain::sink::SinkMetadata;

#[async_trait::async_trait]
pub trait DataInspector: Send + Sync {
    /// Retrieves all available sinks (tables) and their columns.
    async fn get_available_sinks(&self) -> Result<Vec<SinkMetadata>>;

    /// Executes a dynamic query and maps heterogeneous rows to JSON.
    ///
    /// **IMPORTANT: You must ensure `query` is safely constructed to prevent
    /// SQL injection.**
    async fn fetch_dynamic_data(&self, query: &str) -> Result<Vec<Value>>;
}
