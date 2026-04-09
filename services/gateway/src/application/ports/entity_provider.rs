//! Outbound port for retrieving the authorization entity graph.

use anyhow::Result;

use crate::domain::entity::EntityNode;

pub trait EntityGraphProvider: Send + Sync {
    /// Retrieves the entity graph for Cedar.
    async fn get_entity_graph(&self) -> Result<Vec<EntityNode>>;
}
