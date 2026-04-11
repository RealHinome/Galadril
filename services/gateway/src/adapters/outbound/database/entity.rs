//! PostgreSQL and Apache AGE implementation of the EntityGraphProvider port.

use std::collections::HashMap;

use anyhow::{Context, Result};
use sqlx::{PgPool, Row};

use crate::application::ports::entity_provider::EntityGraphProvider;
use crate::domain::entity::{EntityNode, EntityReference};

/// PostgreSQL adapter using Apache AGE to query authorization hierarchies.
pub struct PgAgeEntityProvider {
    pool: PgPool,
    graph_name: String,
}

impl PgAgeEntityProvider {
    /// Creates a new [`PgAgeEntityProvider`].
    pub fn new(pool: PgPool, graph_name: &str) -> Self {
        Self {
            pool,
            graph_name: graph_name.to_string(),
        }
    }
}

#[async_trait::async_trait]
impl EntityGraphProvider for PgAgeEntityProvider {
    async fn get_entity_graph(&self) -> Result<Vec<EntityNode>> {
        let query = format!(
            r#"
            SELECT 
                agtype_to_jsonb(label(n))->>0 AS n_label,
                agtype_to_jsonb(n.id)->>0 AS n_id,
                agtype_to_jsonb(label(p))->>0 AS p_label,
                agtype_to_jsonb(p.id)->>0 AS p_id
            FROM cypher('{}', $$
                MATCH (n)
                OPTIONAL MATCH (n)-[:MEMBER_OF]->(p)
                RETURN n, p
            $$) AS (n agtype, p agtype)
            "#,
            self.graph_name
        );

        let rows = sqlx::query(&query)
            .fetch_all(&self.pool)
            .await
            .context("Failed to fetch entity graph from Apache AGE")?;

        let mut nodes_map: HashMap<String, EntityNode> = HashMap::new();

        for row in rows {
            let n_label: Option<String> = row.try_get("n_label")?;
            let n_id: Option<String> = row.try_get("n_id")?;
            let p_label: Option<String> = row.try_get("p_label")?;
            let p_id: Option<String> = row.try_get("p_id")?;

            if let (Some(n_type), Some(n_identity)) = (n_label, n_id) {
                let node_key = format!("{}::{}", n_type, n_identity);

                let node = nodes_map.entry(node_key).or_insert(EntityNode {
                    entity_type: n_type,
                    entity_id: n_identity,
                    parents: Vec::new(),
                });

                if let (Some(p_type), Some(p_identity)) = (p_label, p_id) {
                    node.parents.push(EntityReference {
                        entity_type: p_type,
                        entity_id: p_identity,
                    });
                }
            }
        }

        Ok(nodes_map.into_values().collect())
    }
}
