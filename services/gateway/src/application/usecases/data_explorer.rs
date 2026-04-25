//! Use cases for exploring and querying data with fine-grained access control.

use std::sync::Arc;
use std::time::{Duration, Instant};

use anyhow::{Result, bail};
use serde_json::Value;
use tokio::sync::RwLock;

use crate::application::ports::data_inspector::DataInspector;
use crate::application::usecases::authorization::{
    Action, AuthService, QueryContext,
};
use crate::domain::sink::SinkMetadata;

const ALLOWED_TABLES: &[&str] = &["entity_states", "entity_embeddings"];

/// Internal cache structure for available tables.
struct TableCache {
    tables: Arc<Vec<SinkMetadata>>,
    expires_at: Instant,
}

/// Service responsible for fetching data securely with FGAC.
pub struct DataExplorerService {
    data_introspector: Arc<dyn DataInspector>,
    auth_service: Arc<AuthService>,
    cache: RwLock<Option<TableCache>>,
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

    pub async fn invalidate_cache(&self) {
        let mut cache_guard = self.cache.write().await;
        *cache_guard = None;
    }

    async fn get_allowed_tables(&self) -> Result<Arc<Vec<SinkMetadata>>> {
        {
            let cache_guard = self.cache.read().await;
            if let Some(cache) = &*cache_guard
                && cache.expires_at > Instant::now()
            {
                return Ok(Arc::clone(&cache.tables));
            }
        }

        let all_tables = self.data_introspector.get_available_sinks().await?;

        let filtered_tables: Vec<SinkMetadata> = all_tables
            .into_iter()
            .filter(|t| ALLOWED_TABLES.contains(&t.name.as_str()))
            .collect();

        let arc_tables = Arc::new(filtered_tables);

        let mut cache_guard = self.cache.write().await;
        *cache_guard = Some(TableCache {
            tables: Arc::clone(&arc_tables),
            expires_at: Instant::now() + self.cache_ttl,
        });

        Ok(arc_tables)
    }

    pub async fn get_authorized_tables(
        &self,
        user_id: &str,
    ) -> Result<Vec<SinkMetadata>> {
        let tables = self.get_allowed_tables().await?;
        let table_names: Vec<String> =
            tables.iter().map(|s| s.name.clone()).collect();

        let allowed_names = self
            .auth_service
            .filter_authorized_resources(
                user_id,
                Action::DiscoverTables,
                &table_names,
            )
            .await?;

        let authorized_tables = tables
            .iter()
            .filter(|s| allowed_names.contains(&s.name))
            .cloned()
            .collect();

        Ok(authorized_tables)
    }

    /// Queries a specific table applying fine-grained Row-Level filters
    /// safely.
    pub async fn query_table(
        &self,
        user_id: &str,
        table_name: &str,
        limit: usize,
        query_context: Option<QueryContext>,
    ) -> Result<Vec<Value>> {
        if !ALLOWED_TABLES.contains(&table_name) {
            bail!("Table '{table_name}' is not allowed or does not exist");
        }

        let safe_limit = limit.clamp(1, 1000);

        let is_allowed = self
            .auth_service
            .is_authorized(
                user_id,
                Action::ReadTable,
                table_name,
                query_context.as_ref(),
            )
            .await?;

        if !is_allowed {
            bail!(
                "User '{user_id}' is not authorized to read from table '{table_name}' with the requested context",
            );
        }

        let mut conditions = Vec::new();

        if let Some(ctx) = query_context {
            if let Some(eid) = ctx.entity_id {
                if !is_safe_identifier(&eid) {
                    bail!("Invalid entity_id format");
                }
                conditions.push(format!("entity_id = '{eid}'"));
            }
            if let Some(modality) = ctx.modality {
                if !is_safe_identifier(&modality) {
                    bail!("Invalid modality format");
                }
                conditions.push(format!("modality = '{modality}'"));
            }
            if let Some(st) = ctx.state_type {
                if !is_safe_identifier(&st) {
                    bail!("Invalid state_type format");
                }
                conditions.push(format!("state_type = '{st}'"));
            }
            if let Some(zone) = ctx.gis_zone {
                // TODO: PostGIS integration.
                if !is_safe_identifier(&zone) {
                    bail!("Invalid gis_zone format");
                }
                conditions.push(format!("metadata->>'zone' = '{zone}'"));
            }
        }

        let where_clause = if conditions.is_empty() {
            String::new()
        } else {
            format!("WHERE {}", conditions.join(" AND "))
        };

        let query = format!(
            r#"SELECT * FROM "{table_name}" {where_clause} LIMIT {safe_limit}"#
        );

        self.data_introspector.fetch_dynamic_data(&query).await
    }
}

/// Validates that a string only contains safe characters to prevent SQL
/// injection.
fn is_safe_identifier(val: &str) -> bool {
    val.chars()
        .all(|c| c.is_ascii_alphanumeric() || c == '_' || c == '-')
}
