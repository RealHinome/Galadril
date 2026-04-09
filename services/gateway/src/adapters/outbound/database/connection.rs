//! Database connection management.

use std::str::FromStr;

use anyhow::{Context, Result};
use sqlx::postgres::{PgConnectOptions, PgPoolOptions};
use sqlx::{Executor, PgPool};

/// Establishes a Postgres connection pool with the Apache AGE extension
/// loaded.
pub async fn create_pool(database_url: &str) -> Result<PgPool> {
    let options = PgConnectOptions::from_str(database_url)
        .context("Failed to parse database URL")?;

    let pool = PgPoolOptions::new()
        .max_connections(10)
        .after_connect(|conn, _meta| {
            Box::pin(async move {
                conn.execute("LOAD 'age'; SET search_path = ag_catalog, \"$user\", public;")
                    .await?;
                Ok(())
            })
        })
        .connect_with(options)
        .await
        .context("Failed to create PostgreSQL connection pool")?;

    Ok(pool)
}
