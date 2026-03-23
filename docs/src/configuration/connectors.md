# Connector

`connectors` defines infrastructure credentials for external services.

```yaml
name: connector_example

connectors:
  # Streaming ingestion for incoming events.
  kafka:
    brokers: ["redpanda:9092"]
    schema_registry: "http://redpanda:8081"
    consumer_group: "intake-service"

  # Storage for processed raw documents.
  s3:
    endpoint: "http://minio:9000"
    access_key: "minioadmin"
    secret_key: "minioadmin"
    region: "us-east-1"
    bucket_notifications: "s3-bucket-notifications"

  # Persistent storage.
  postgres:
    database: "galadril_dev"
    host: "postgres:5432"
    user: "postgres"
    password: "postgres"
```

(This example relies on Docker network.)

### 1. Kafka Connector

* **brokers**: A list of bootstrap servers (e.g., Redpanda or Apache Kafka).
* **schema_registry**: The URL for the Confluent-compatible schema management
    service for managing data formats.
* **consumer_group**: The logical identifier that allows multiple workers to
    share the processing load of a topic.

### 2. S3 (Object Storage) Connector
Used for storing and retrieving large binary objects like images, videos, or
model weights.
* **endpoint**: The API entry point. This allows for compatibility between
    local solutions like MinIO and cloud providers like AWS.
* **access_key / secret_key**: The credentials required for secure
    authentication.
* **bucket_notifications**: Defines the specific topic or queue where bucket
    events (like "Object Created") are published.

### 3. Postgres Connector
Manages relational data, system state, and metadata.
* **host**: The network address and port of the database instance.
* **database**: The specific database name for the application environment.
* **user / password**: The credentials used to establish a secure database
    session.
