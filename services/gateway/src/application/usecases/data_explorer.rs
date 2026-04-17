//! Use cases for exploring and querying heterogeneous data sinks with caching.

use std::sync::Arc;
use std::time::{Duration, Instant};

use anyhow::{Result, bail};
use serde_json::Value;
use tokio::sync::RwLock;

use crate::application::ports::data_inspector::DataInspector;
use crate::application::usecases::authorization::{Action, AuthService};
use crate::domain::sink::SinkMetadata;

/// Internal cache structure for available sinks.
struct SinkCache {
    sinks: Arc<Vec<SinkMetadata>>,
    expires_at: Instant,
}

/// Service responsible for fetching data and metadata.
pub struct DataExplorerService {
    data_introspector: Arc<dyn DataInspector>,
    auth_service: Arc<AuthService>,
    cache: RwLock<Option<SinkCache>>,
    cache_ttl: Duration,
}

impl DataExplorerService {
    /// Creates a new [`DataExplorerService`].
    pub fn new(
        data_introspector: Arc<dyn DataInspector>,
        auth_service: Arc<AuthService>,
        cache_ttl: Duration,
    ) -> Self {
        Self {
            data_introspector,
            auth_service,
            cache: RwLock::new(None),
            cache_ttl,
        }
    }

    /// Explicitly invalidates the cache.
    pub async fn invalidate_cache(&self) {
        let mut cache_guard = self.cache.write().await;
        *cache_guard = None;
    }

    /// Fetches all available sinks from cache or database.
    async fn get_all_sinks(&self) -> Result<Arc<Vec<SinkMetadata>>> {
        {
            let cache_guard = self.cache.read().await;
            if let Some(cache) = &*cache_guard &&
                cache.expires_at > Instant::now()
            {
                return Ok(Arc::clone(&cache.sinks));
            }
        }

        let sinks = self.data_introspector.get_available_sinks().await?;
        let arc_sinks = Arc::new(sinks);

        let mut cache_guard = self.cache.write().await;
        *cache_guard = Some(SinkCache {
            sinks: Arc::clone(&arc_sinks),
            expires_at: Instant::now() + self.cache_ttl,
        });

        Ok(arc_sinks)
    }

    /// Retrieves a list of sinks the user is explicitly authorized to
    /// discover.
    pub async fn get_authorized_sinks(
        &self,
        user_id: &str,
    ) -> Result<Vec<SinkMetadata>> {
        let all_sinks = self.get_all_sinks().await?;
        let sink_names: Vec<String> =
            all_sinks.iter().map(|s| s.name.clone()).collect();

        let allowed_names = self
            .auth_service
            .filter_authorized_resources(
                user_id,
                Action::DiscoverSinks,
                &sink_names,
            )
            .await?;

        let authorized_sinks = all_sinks
            .iter()
            .filter(|s| allowed_names.contains(&s.name))
            .cloned()
            .collect();

        Ok(authorized_sinks)
    }

    /// Queries a specific sink if the user has read permissions.
    pub async fn query_sink(
        &self,
        user_id: &str,
        sink_name: &str,
        limit: usize,
    ) -> Result<Vec<Value>> {
        if !sink_name
            .chars()
            .all(|c| c.is_ascii_alphanumeric() || c == '_')
        {
            bail!("Invalid sink name format");
        }

        let safe_limit = limit.clamp(1, 1000);

        let is_allowed = self
            .auth_service
            .is_authorized(user_id, Action::ReadSink, sink_name)
            .await?;

        if !is_allowed {
            bail!(
                "User '{user_id}' is not authorized to read from sink '{sink_name}'",
            );
        }

        let all_sinks = self.get_all_sinks().await?;
        if !all_sinks.iter().any(|s| s.name == sink_name) {
            bail!("Sink '{sink_name}' does not exist in the database");
        }

        let query =
            format!(r#"SELECT * FROM "{sink_name}" LIMIT {safe_limit}"#);
        self.data_introspector.fetch_dynamic_data(&query).await
    }
}
