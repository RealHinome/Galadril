# Data Parsers

Once a file is routed to a source, the `parser` dictates how the file's content
is transformed before entering Kafka.

## 1. The `metadata` Parser (Default)

* **Behavior**: Does *not* download the file. It generates a standard JSON
    payload containing the S3 URI, timestamps, and generated UUIDs.
* **Use Case**: Images, Videos, PDFs. You don't want 50MB images flowing
    through Kafka. You pass the reference (URI), and the Python Vision service
    will download it later.

## 2. The `csv` Parser

* **Behavior**: Downloads the file from S3 and parses it line by line using the
    CSV headers. It emits **one Kafka message per row**. It automatically
    converts numerical strings to floats.
* **Use Case**: Batch ingestion of financial transactions, lists of employees,
    or sensor logs.

## 3. The `json` Parser

* **Behavior**: Downloads the file. If the file contains a JSON Array, it emits
    **one Kafka message per item**. If it's a single JSON Object, it emits one
    message.
* **Use Case**: OSINT data, scraped articles, or API data dumps.

### Example

```yaml
sources:
  - id: financial_data
    topic: raw.finance
    parser: csv
    match_pattern: "^finance/.*\\.csv$"
    schema_path: schemas/avro/finance.avsc
````
