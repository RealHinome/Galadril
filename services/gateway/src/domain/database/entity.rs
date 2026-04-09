//! Authorization entity graph value objects.

/// Node in the authorization graph.
#[derive(Debug, Clone)]
pub struct EntityNode {
    /// The type of the entity (e.g., "User", "Role", "Sink").
    pub entity_type: String,
    pub entity_id: String,
    /// The parent entities this node belongs to.
    pub parents: Vec<EntityReference>,
}

/// Represents a reference to a parent entity in the graph.
#[derive(Debug, Clone)]
pub struct EntityReference {
    pub entity_type: String,
    pub entity_id: String,
}
