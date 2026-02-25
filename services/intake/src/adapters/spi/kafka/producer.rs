//! Kafka producer.

use std::collections::HashMap;
use std::time::Duration;

use anyhow::{Context, Result, anyhow};
use async_trait::async_trait;
use rdkafka::config::ClientConfig;
use rdkafka::producer::{FutureProducer, FutureRecord};
use schema_registry_converter::async_impl::avro::AvroEncoder;
use schema_registry_converter::async_impl::schema_registry::{
    SrSettings, post_schema,
};
use schema_registry_converter::schema_registry_common::{
    SchemaType, SubjectNameStrategy, SuppliedSchema,
};
use serde::Serialize;

use crate::domain::models::{
    DocumentMetadata, FinancialTransaction, OsintArticle,
    SatelliteImageMetadata,
};
use crate::domain::ports::EventProducer;

const DOCUMENT_NAMESPACE: &str = "com.galadril.raw.document.DocumentMetadata";
const FINANCE_NAMESPACE: &str =
    "com.galadril.raw.financial.FinancialTransaction";
const OSINT_NAMESPACE: &str = "com.galadril.raw.osint.OsintArticle";
const SATELLITE_NAMESPACE: &str =
    "com.galadril.raw.satellite.SatelliteImageMetadata";

pub struct KafkaProducerAdapter {
    producer: FutureProducer,
    topic: String,
    encoder: AvroEncoder<'static>,
    schema_names: HashMap<String, String>,
}

impl KafkaProducerAdapter {
    /// Create a new [`KafkaProducerAdapter`].
    pub async fn new(
        brokers: &str,
        registry_url: &str,
        topic: &str,
    ) -> Result<Self> {
        let config = ClientConfig::new()
            .set("bootstrap.servers", brokers)
            .set("message.timeout.ms", "5000")
            .set("acks", "all")
            .clone();

        crate::adapters::spi::kafka::create_topics(&config, topic).await?;

        let producer: FutureProducer =
            config.create().context("Failed to create Kafka producer")?;

        let sr_settings = SrSettings::new_builder(registry_url.to_string())
            .build()
            .context("Failed to create Schema Registry settings")?;
        let schema_names = Self::register_schemas(&sr_settings).await?;
        let encoder = AvroEncoder::new(sr_settings);

        tracing::info!(?brokers, "kafka producer ready");

        Ok(Self {
            producer,
            topic: topic.to_string(),
            encoder,
            schema_names,
        })
    }

    async fn register_schemas(
        sr_settings: &SrSettings,
    ) -> Result<HashMap<String, String>> {
        let schemas_to_register = vec![
            (
                DOCUMENT_NAMESPACE,
                include_str!("../../../../../../schemas/avro/document.avsc"),
            ),
            (
                FINANCE_NAMESPACE,
                include_str!("../../../../../../schemas/avro/finance.avsc"),
            ),
            (
                OSINT_NAMESPACE,
                include_str!("../../../../../../schemas/avro/osint.avsc"),
            ),
            (
                SATELLITE_NAMESPACE,
                include_str!("../../../../../../schemas/avro/satellite.avsc"),
            ),
        ];

        let mut schema_mapping = HashMap::new();

        for (key, schema_raw) in schemas_to_register {
            let parsed_schema = apache_avro::Schema::parse_str(schema_raw)
                .context(format!("Failed to parse schema for {key}"))?;

            let record_name = match &parsed_schema {
                apache_avro::Schema::Record(record) => {
                    record.name.fullname(None)
                },
                _ => {
                    return Err(anyhow!(
                        "Schema {key:?} is not a record type"
                    ));
                },
            };

            let subject = format!("{record_name}-value");

            let supplied_schema = SuppliedSchema {
                name: Some(record_name.clone()),
                schema_type: SchemaType::Avro,
                schema: schema_raw.to_string(),
                references: vec![],
                properties: None,
                tags: None,
            };

            post_schema(sr_settings, subject.clone(), supplied_schema)
                .await
                .context(format!("Failed to register schema for {key}"))?;

            tracing::info!(?record_name, "schema registered as {key:?}");

            schema_mapping.insert(key.to_string(), record_name);
        }

        Ok(schema_mapping)
    }

    async fn send<T: Serialize>(
        &self,
        key: &str,
        schema_key: &str,
        payload: &T,
    ) -> Result<()> {
        let record_name =
            self.schema_names.get(schema_key).ok_or_else(|| {
                anyhow!("Schema key {schema_key:?} not recognized")
            })?;

        let strategy =
            SubjectNameStrategy::RecordNameStrategy(record_name.clone());

        let encoded = self
            .encoder
            .encode_struct(payload, &strategy)
            .await
            .context(format!(
                "Failed to encode payload for schema {record_name:?}"
            ))?;

        let record = FutureRecord::to(&self.topic).key(key).payload(&encoded);

        self.producer
            .send(record, Duration::from_secs(5))
            .await
            .map_err(|(err, _)| anyhow!("Kafka send error: {err:?}"))?;

        tracing::debug!(?record_name, "event sent");

        Ok(())
    }
}

#[async_trait]
impl EventProducer for KafkaProducerAdapter {
    async fn publish_financial(
        &self,
        event: FinancialTransaction,
    ) -> Result<()> {
        self.send(&event.transaction_id, FINANCE_NAMESPACE, &event)
            .await
    }

    async fn publish_satellite_meta(
        &self,
        meta: SatelliteImageMetadata,
    ) -> Result<()> {
        self.send(&meta.image_id, SATELLITE_NAMESPACE, &meta).await
    }

    async fn publish_osint(&self, article: OsintArticle) -> Result<()> {
        self.send(&article.article_id, OSINT_NAMESPACE, &article)
            .await
    }

    async fn publish_document(&self, doc: DocumentMetadata) -> Result<()> {
        self.send(&doc.document_id, DOCUMENT_NAMESPACE, &doc).await
    }
}
