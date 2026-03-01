use anyhow::Result;

/// Trait that library consumers implement to provide data lookup capabilities
/// to the NLP model during report generation.
///
/// The model calls `from_database(query)` when it needs external data before
/// writing a section. Implement this trait to connect to any backend.
#[async_trait::async_trait]
pub trait DatabaseProvider: Send + Sync {
    /// Execute a lookup query requested by the model.
    async fn from_database(&self, query: &str) -> Result<Option<String>>;
}

/// Default no-op provider. Always returns `None`.
pub struct NoOpProvider;

#[async_trait::async_trait]
impl DatabaseProvider for NoOpProvider {
    async fn from_database(&self, _query: &str) -> Result<Option<String>> {
        Ok(None)
    }
}
