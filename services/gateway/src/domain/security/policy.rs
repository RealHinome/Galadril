//! Cedar policy value objects.

/// Represents a Cedar policy retrieved from the database.
#[derive(Debug, Clone)]
pub struct PolicyRecord {
    pub id: String,
    pub content: String,
}
