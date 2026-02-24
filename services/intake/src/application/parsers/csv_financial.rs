//! Custom CSV parser for financial data.
//!
//! Require: `amount`, `currency` and `timestamp`.

use std::sync::Arc;

use anyhow::{Result, anyhow};
use chrono::{DateTime, Utc};
use uuid::Uuid;

use crate::domain::models::FinancialTransaction;
use crate::domain::ports::EventProducer;

pub struct CsvFinancialParser;

impl CsvFinancialParser {
    /// Parse the CSV content line by line and publish each transaction.
    pub async fn parse_and_publish(
        content: &[u8],
        producer: &Arc<dyn EventProducer>,
    ) -> Result<()> {
        let mut reader = csv::ReaderBuilder::new()
            .has_headers(true)
            .from_reader(content);

        let mut line_number: usize = 1; // CSV header is line 0.

        for result in reader.deserialize() {
            line_number += 1;

            let record: CsvFinancialRow = result?;
            let transaction = Self::validate_and_map(record, line_number)?;
            producer.publish_financial(transaction).await?;
        }
        tracing::debug!(?line_number, "analyzed csv");

        Ok(())
    }

    fn validate_and_map(
        row: CsvFinancialRow,
        line: usize,
    ) -> Result<FinancialTransaction> {
        if row.amount <= 0.0 {
            return Err(anyhow!(
                "Line {line}: amount must be positive, got {}",
                row.amount
            ));
        }

        // Check for ISO 4217.
        if row.currency.len() != 3 {
            return Err(anyhow!(
                "Line {line}: currency must be ISO 4217 (3 chars), got {:?}",
                row.currency
            ));
        }

        let timestamp =
            row.timestamp.parse::<DateTime<Utc>>().map_err(|err| {
                anyhow!(
                    "Line {line}: invalid timestamp {:?}: {err:?}",
                    row.timestamp
                )
            })?;

        Ok(FinancialTransaction {
            event_id: Uuid::new_v4().to_string(),
            transaction_id: row.transaction_id,
            timestamp,
            sender_account: row.sender_account,
            receiver_account: row.receiver_account,
            amount: row.amount,
            currency: row.currency.to_uppercase(),
            transaction_type: row.transaction_type,
            source_system: row.source_system,
        })
    }
}

#[derive(Debug, serde::Deserialize)]
struct CsvFinancialRow {
    transaction_id: String,
    timestamp: String,
    sender_account: String,
    receiver_account: String,
    amount: f64,
    currency: String,
    transaction_type: Option<String>,
    source_system: String,
}
