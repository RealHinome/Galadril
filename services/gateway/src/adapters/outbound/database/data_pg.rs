//! PostgreSQL implementation of DataInspector port.

use std::collections::HashMap;

use anyhow::{Context, Result};
use pgvector::Vector;
use serde_json::{Map, Value};
use sqlx::{Column, PgPool, Row, TypeInfo};

use crate::application::ports::data_inspector::DataInspector;
use crate::domain::sink::SinkMetadata;

/// PostgreSQL adapter for introspecting and querying dynamic schemas.
pub struct PgDataIntrospector {
    pool: PgPool,
}

impl PgDataIntrospector {
    /// Creates a new [`PgDataIntrospector`].
    pub fn new(pool: PgPool) -> Self {
        Self { pool }
    }
}

impl DataInspector for PgDataIntrospector {
    async fn get_available_sinks(&self) -> Result<Vec<SinkMetadata>> {
        let rows = sqlx::query(
            r#"
            SELECT table_name, column_name 
            FROM information_schema.columns 
            WHERE table_schema = 'public'
            ORDER BY table_name, ordinal_position
            "#
        )
        .fetch_all(&self.pool)
        .await
        .context("Failed to fetch information schema")?;

        let mut sinks_map: HashMap<String, Vec<String>> = HashMap::new();
        
        for row in rows {
            let table_name: Option<String> = row.try_get("table_name")?;
            let column_name: Option<String> = row.try_get("column_name")?;

            if let (Some(table), Some(column)) = (table_name, column_name) {
                sinks_map.entry(table).or_default().push(column);
            }
        }

        let sinks = sinks_map
            .into_iter()
            .map(|(name, columns)| SinkMetadata { name, columns })
            .collect();

        Ok(sinks)
    }

    async fn fetch_dynamic_data(&self, query: &str) -> Result<Vec<Value>> {
        let rows = sqlx::query(query)
            .fetch_all(&self.pool)
            .await
            .context("Failed to execute dynamic query")?;

        let mut results = Vec::with_capacity(rows.len());

        for row in rows {
            let mut json_obj = Map::new();

            for (i, column) in row.columns().iter().enumerate() {
                let col_name = column.name();
                let type_name = column.type_info().name();

                let json_value = match type_name {
                    "TEXT" | "VARCHAR" | "NAME" => {
                        let val: Option<String> = row.try_get(i)?;
                        val.map(Value::String).unwrap_or(Value::Null)
                    },
                    "INT4" => {
                        let val: Option<i32> = row.try_get(i)?;
                        val.map(|v| Value::Number(v.into()))
                            .unwrap_or(Value::Null)
                    },
                    "INT8" => {
                        let val: Option<i64> = row.try_get(i)?;
                        val.map(|v| Value::Number(v.into()))
                            .unwrap_or(Value::Null)
                    },
                    "FLOAT4" => {
                        let val: Option<f32> = row.try_get(i)?;
                        val.and_then(|v| {
                            serde_json::Number::from_f64(v as f64)
                                .map(Value::Number)
                        })
                        .unwrap_or(Value::Null)
                    },
                    "FLOAT8" => {
                        let val: Option<f64> = row.try_get(i)?;
                        val.and_then(|v| {
                            serde_json::Number::from_f64(v).map(Value::Number)
                        })
                        .unwrap_or(Value::Null)
                    },
                    "BOOL" => {
                        let val: Option<bool> = row.try_get(i)?;
                        val.map(Value::Bool).unwrap_or(Value::Null)
                    },
                    "JSON" | "JSONB" => {
                        // Handles Apache AGE agtype when casted to ::jsonb in
                        // the query
                        let val: Option<Value> = row.try_get(i)?;
                        val.unwrap_or(Value::Null)
                    },
                    "vector" => {
                        let val: Option<Vector> = row.try_get(i)?;
                        match val {
                            Some(vec) => {
                                let floats: Vec<Value> = vec
                                    .to_vec()
                                    .into_iter()
                                    .filter_map(|f| {
                                        serde_json::Number::from_f64(f as f64)
                                    })
                                    .map(Value::Number)
                                    .collect();
                                Value::Array(floats)
                            },
                            None => Value::Null,
                        }
                    },
                    _ => {
                        let val: Option<String> =
                            row.try_get(i).unwrap_or(None);
                        val.map(Value::String).unwrap_or(Value::Null)
                    },
                };

                json_obj.insert(col_name.to_string(), json_value);
            }
            results.push(Value::Object(json_obj));
        }

        Ok(results)
    }
}
