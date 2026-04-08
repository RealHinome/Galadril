//! Outbound port for Cedar policy retrieval.

use anyhow::Result;

use crate::domain::policy::PolicyRecord;

pub trait PolicyStore: Send + Sync {
    /// Retrieves all active Cedar policies from the store.
    async fn get_active_policies(&self) -> Result<Vec<PolicyRecord>>;
}
