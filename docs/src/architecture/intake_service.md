# Intake service

Intake service is a Rust binary located in `services/intake/`. Its sole
responsibility is ingestion.

## Initialization Phase

When the service boots up:
1. It reads `pipeline.yaml`.
2. It loops through all defined `sources`.
3. If a source defines an Avro `schema_path`, the service registers this schema
    with the Confluent Schema Registry.
4. It creates the required Kafka topics if they do not exist.

## The Event Loop
The service continuously listens to the S3 bucket notification topic. When a
    file arrives:
1. **Routing**: It compares the S3 file path against the YAML configuration to
    find a match.
2. **Parsing**: It dynamically selects the correct parser (e.g., CSV, JSON)
3. **Emitting**: It encodes the parsed data (in Avro or JSON) and publishes it
    to the designated Kafka topic.
