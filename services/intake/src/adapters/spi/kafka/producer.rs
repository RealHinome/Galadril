//! Kafka producer.

use std::time::Duration;

use anyhow::{Context, Result, anyhow};
use apache_avro::{Schema, to_avro_datum};
use async_trait::async_trait;
use rdkafka::config::ClientConfig;
use rdkafka::producer::{FutureProducer, FutureRecord};
use serde::Serialize;

use crate::domain::models::{
    DocumentMetadata, FinancialTransaction, OsintArticle,
    SatelliteImageMetadata,
};
use crate::domain::ports::EventProducer;

pub struct KafkaProducerAdapter {
    producer: FutureProducer,
    topic: String,
    schemas: AvroSchemas,
}

struct AvroSchemas {
    financial: Schema,
    satellite: Schema,
    osint: Schema,
    document: Schema,
}

impl KafkaProducerAdapter {
    /// Create a new [`KafkaProducerAdapter`].
    pub fn new(brokers: &str, topic: &str) -> Result<Self> {
        let producer: FutureProducer = ClientConfig::new()
            .set("bootstrap.servers", brokers)
            .set("message.timeout.ms", "5000")
            .set("acks", "all") // Durabilité maximale
            .create()
            .context("Failed to create Kafka producer")?;

        let schemas = AvroSchemas {
            financial: Schema::parse_str(include_str!(
                "../../../../../../schemas/avro/finance.avsc"
            ))?,
            satellite: Schema::parse_str(include_str!(
                "../../../../../../schemas/avro/satellite.avsc"
            ))?,
            osint: Schema::parse_str(include_str!(
                "../../../../../../schemas/avro/osint.avsc"
            ))?,
            document: Schema::parse_str(include_str!(
                "../../../../../../schemas/avro/document.avsc"
            ))?,
        };

        Ok(Self {
            producer,
            topic: topic.to_string(),
            schemas,
        })
    }

    /// Serialize in Avro and send on topic.
    async fn send<T: Serialize>(
        &self,
        topic: &str,
        key: &str,
        schema: &Schema,
        payload: &T,
    ) -> Result<()> {
        let avro_value = apache_avro::to_value(payload)?;

        let encoded = to_avro_datum(schema, avro_value)?;

        let record = FutureRecord::to(topic).key(key).payload(&encoded);

        self.producer
            .send(record, Duration::from_secs(5))
            .await
            .map_err(|(err, _)| anyhow!("Kafka send error: {err:?}"))?;

        Ok(())
    }
}

#[async_trait]
impl EventProducer for KafkaProducerAdapter {
    async fn publish_financial(
        &self,
        event: FinancialTransaction,
    ) -> Result<()> {
        self.send(
            &self.topic,
            &event.transaction_id,
            &self.schemas.financial,
            &event,
        )
        .await
    }

    async fn publish_satellite_meta(
        &self,
        meta: SatelliteImageMetadata,
    ) -> Result<()> {
        self.send(&self.topic, &meta.image_id, &self.schemas.satellite, &meta)
            .await
    }

    async fn publish_osint(&self, article: OsintArticle) -> Result<()> {
        self.send(
            &self.topic,
            &article.article_id,
            &self.schemas.osint,
            &article,
        )
        .await
    }

    async fn publish_document(&self, doc: DocumentMetadata) -> Result<()> {
        self.send(&self.topic, &doc.document_id, &self.schemas.document, &doc)
            .await
    }
}
