# Internal Architecture

Galadril is divided into three distinct operational layers (Medaillon
architecture):

1. **The Synapse**: MinIO (S3) and Redpanda (Kafka).
2. **The Ingestor**: A Rust service that catches raw data and normalizes it.
3. **The Vision**: A Python service that applies AI models and extracts
    insights.
