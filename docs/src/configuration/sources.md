# Data Sources & Routing

`sources` defines how raw files in S3 are caught and routed into Kafka.
```yaml
sources:
  - id: image_source
    match_pattern: "^images/" # support Regexes!
    topic: raw_images
    schema_path: schemas/avro/image.avsc
```

## Definition Fields

| Field | Type | Description |
|---|---|---|
| `id` | String | Unique identifier for this source. |
| `topic` | String | Kafka topic where parsed data will be sent. |
| `schema_path` | String | *(Optional)* Local path to an `.avsc` Avro schema. |
| `match_pattern` | String | *(Optional)* Regex to identify where to stream. |
| `parser` | String | See [Data Parsers](/configuration/parsers.md). |

## How Routing Works

When a file arrives in S3 (e.g., `s3://my-bucket/finance/january.csv`),
the Rust Ingestor must decide which source block to use.

**1. Regex Matching (`match_pattern`)**

If you define `match_pattern: "^finance/.*\.csv$"`, the system will test the S3
key against this regex. If it matches, this source is selected.

**2. Otherwise**

If no `match_pattern` is defined, the system will reject the incoming source, 
and won't process the raw data.

## Required & Reserved Fields

While Avro is flexible, Galadril's internal logic (especially the Python Vision
service) expects specific fields to be present in the schema to properly link
data back to its origin.

### 1. Unique Identifiers
Every record must have a unique ID. The system looks for these fields in order
of priority to determine the Kafka **partitioning key**:
1. `event_id` (Common for logs/financials)
2. `image_id` (For satellite/photos)
3. `document_id` (For PDFs/Docs)
4. `article_id` (For OSINT/News)

### 2. Traceability Fields
To ensure the Python pipeline can download binary content, the following field
is **mandatory** for `metadata` parsers:
* **`storage_path`** (String): The full S3 URI.
