//! PostgreSQL implementation of the PolicyStore port.

use anyhow::{Context, Result};
use sqlx::{PgPool, Row};

use crate::application::ports::policy_store::PolicyStore;
use crate::domain::policy::PolicyRecord;

/// PostgreSQL adapter for retrieving Cedar policies.
pub struct PgPolicyStore {
    pool: PgPool,
}

impl PgPolicyStore {
    /// Creates a new [`PgPolicyStore`].
    pub fn new(pool: PgPool) -> Self {
        Self { pool }
    }
}

impl PolicyStore for PgPolicyStore {
    async fn get_active_policies(&self) -> Result<Vec<PolicyRecord>> {
        let rows = sqlx::query(
            r#"
            SELECT id, content 
            FROM auth_policies 
            WHERE is_active = true
            "#,
        )
        .fetch_all(&self.pool)
        .await
        .context("Failed to fetch active Cedar policies from database")?;

        let mut records = Vec::with_capacity(rows.len());

        for row in rows {
            let id: String =
                row.try_get("id").context("Missing 'id' column")?;
            let content: String =
                row.try_get("content").context("Missing 'content' column")?;

            records.push(PolicyRecord { id, content });
        }

        Ok(records)
    }
}
