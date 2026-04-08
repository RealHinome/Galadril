//! Sink metadata value objects.

/// Represents a dynamically discovered database table (sink) and its columns.
#[derive(Debug, Clone)]
pub struct SinkMetadata {
    pub name: String,
    pub columns: Vec<String>,
}
