//! Data parser.

use anyhow::{Result, anyhow};
use chrono::Utc;
use serde_json::{Value, json};
use uuid::Uuid;

/// Parse content into generic JSON payloads.
pub fn parse_content(
    parser_type: &str,
    content: &[u8],
    key: &str,
    bucket: &str,
) -> Result<Vec<Value>> {
    match parser_type {
        "csv" => parse_csv(content),
        "json" => parse_json(content),
        "metadata" | "passthrough" => Ok(vec![build_metadata(key, bucket)]),
        _ => Err(anyhow!("Unknown parser type: {}", parser_type)),
    }
}

fn parse_csv(content: &[u8]) -> Result<Vec<Value>> {
    let mut reader = csv::ReaderBuilder::new()
        .has_headers(true)
        .from_reader(content);
    let headers = reader.headers()?.clone();
    let mut records = Vec::new();

    for result in reader.records() {
        let record = result?;
        let mut map = serde_json::Map::new();

        for (i, field) in record.iter().enumerate() {
            let header = headers.get(i).unwrap_or("unknown");

            let val = if let Ok(num) = field.parse::<f64>() {
                json!(num)
            } else if let Ok(b) = field.parse::<bool>() {
                json!(b)
            } else {
                json!(field)
            };
            map.insert(header.to_string(), val);
        }

        if !map.contains_key("event_id") {
            map.insert(
                "event_id".to_string(),
                json!(Uuid::new_v4().to_string()),
            );
        }

        records.push(Value::Object(map));
    }
    Ok(records)
}

fn parse_json(content: &[u8]) -> Result<Vec<Value>> {
    let parsed: Value = serde_json::from_slice(content)?;
    if let Value::Array(arr) = parsed {
        Ok(arr)
    } else {
        Ok(vec![parsed])
    }
}

fn build_metadata(key: &str, bucket: &str) -> Value {
    let storage_path = format!("s3://{}/{}", bucket, key);
    let common_id = Uuid::new_v4().to_string();
    let provider = key.split('/').nth(1).unwrap_or("unknown");

    // We inject all possible IDs so the unified schema works for everything.
    json!({
        "image_id": common_id,
        "document_id": common_id,
        "original_filename": key,
        "storage_path": storage_path,
        "acquisition_date": Utc::now().to_rfc3339(),
        "ingested_at": Utc::now().to_rfc3339(),
        "provider": provider,
        "geometry": {
            "top_left_lat": 0.0,
            "top_left_lon": 0.0,
            "bottom_right_lat": 0.0,
            "bottom_right_lon": 0.0
        },
        "mime_type": "application/octet-stream",
        "file_hash": "",
        "file_size_bytes": 0,
        "source_context": null,
        "metadata_tags": {}
    })
}
