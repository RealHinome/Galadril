use std::sync::{Arc, RwLock};

use anyhow::{Result, anyhow};
use mistralrs::tool;

/// Trait that library consumers implement to provide data lookup capabilities
/// to the NLP model during report generation.
#[async_trait::async_trait]
pub trait DatabaseProvider: Send + Sync {
    /// Execute a lookup query requested by the model.
    #[allow(clippy::wrong_self_convention)]
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

lazy_static::lazy_static! {
    // Global registry using RwLock to avoid Sized trait bound issues.
    pub static ref GLOBAL_DB_PROVIDER: RwLock<Arc<dyn DatabaseProvider>> = RwLock::new(Arc::new(NoOpProvider));
}

/// Sets the global database provider to be used by the MistralRS agent.
pub fn set_database_provider(
    provider: impl DatabaseProvider + 'static,
) -> Result<()> {
    match GLOBAL_DB_PROVIDER.write() {
        Ok(mut guard) => {
            *guard = Arc::new(provider);
            Ok(())
        },
        Err(e) => Err(anyhow!(
            "RwLock poisoned when setting database provider: {}",
            e
        )),
    }
}

/// Query an external database to retrieve context data before writing a
/// section.
#[tool(
    description = "Query an external GraphRAG/Ontology database to retrieve verified facts, military metrics, or structured intelligence data before writing a section. Use this strictly to ground your knowledge and avoid hallucinations."
)]
pub async fn from_database(
    #[description = "A precise natural-language query describing the specific intelligence or data needed."]
    query: String,
) -> Result<String> {
    tracing::info!(?query, "from_database tool invoked by agent");

    let provider = match GLOBAL_DB_PROVIDER.read() {
        Ok(guard) => guard.clone(),
        Err(e) => {
            return Err(anyhow!(
                "RwLock poisoned when reading database provider: {}",
                e
            ));
        },
    };

    match provider.from_database(&query).await? {
        Some(result) => Ok(result),
        None => Ok("No relevant data found in the database for your query. Do not hallucinate data; instead, note the absence of intelligence if applicable.".to_string()),
    }
}
