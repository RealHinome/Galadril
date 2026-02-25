"""Kafka consumer for heterogeneous input messages."""

from __future__ import annotations

from collections.abc import Iterator
from typing import TYPE_CHECKING

import orjson
import structlog
from confluent_kafka import Consumer, KafkaError
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.avro import AvroDeserializer

from galadril_vision.common.exceptions import KafkaConsumerError
from galadril_vision.connectors.kafka.schemas import (
    DocumentMessage,
    FinancialTransactionMessage,
    InputType,
    OsintArticleMessage,
    SatelliteImageMessage,
    UnifiedInputRecord,
)

if TYPE_CHECKING:
    from galadril_vision.config import KafkaConfig

logger = structlog.get_logger(__name__)

_TOPIC_TYPE_MAP = {
    "galadril.raw.satellite": InputType.SATELLITE_IMAGE,
    "galadril.raw.document": InputType.DOCUMENT,
    "galadril.raw.osint": InputType.OSINT_ARTICLE,
    "galadril.raw.financial": InputType.FINANCIAL_TRANSACTION,
}


class KafkaMultiTopicConsumer:
    """Consume heterogeneous messages from multiple Kafka topics."""

    def __init__(
        self,
        config: KafkaConfig,
        schema_registry_url: str | None = None,
    ) -> None:
        self._config = config
        self._consumer: Consumer | None = None
        self._schema_registry_url = schema_registry_url
        self._deserializers: dict[str, AvroDeserializer] = {}

    def connect(self) -> None:
        """Initialize the Kafka consumer with multi-topic subscription."""
        conf = {
            "bootstrap.servers": self._config.bootstrap_servers,
            "group.id": self._config.group_id,
            "auto.offset.reset": self._config.auto_offset_reset,
            "enable.auto.commit": self._config.enable_auto_commit,
            "session.timeout.ms": self._config.session_timeout_ms,
        }

        self._consumer = Consumer(conf)

        topics = list(_TOPIC_TYPE_MAP.keys())
        self._consumer.subscribe(topics)

        if self._schema_registry_url:
            self._init_deserializers()

        logger.info(
            "kafka_consumer_connected",
            topics=topics,
            group_id=self._config.group_id,
        )

    def _init_deserializers(self) -> None:
        """Initialize Avro deserializers for each topic."""
        sr_client = SchemaRegistryClient({"url": self._schema_registry_url})

        for topic in _TOPIC_TYPE_MAP:
            try:
                self._deserializers[topic] = AvroDeserializer(
                    sr_client,
                    schema_str=None,  # TODO: Fetch from registry.
                )
            except Exception as exc:
                logger.warning(
                    "deserializer_init_failed",
                    topic=topic,
                    error=str(exc),
                )

    def _parse_message(
        self,
        topic: str,
        value: bytes,
    ) -> UnifiedInputRecord | None:
        """Parse a message based on its topic."""
        try:
            # Use Avro deserializer if available, otherwise JSON.
            if topic in self._deserializers:
                payload = self._deserializers[topic](value, None)
            else:
                payload = orjson.loads(value)

            input_type = _TOPIC_TYPE_MAP.get(topic)

            match input_type:
                case InputType.SATELLITE_IMAGE:
                    msg = SatelliteImageMessage.model_validate(payload)
                    return UnifiedInputRecord.from_satellite(msg)

                case InputType.DOCUMENT:
                    msg = DocumentMessage.model_validate(payload)
                    return UnifiedInputRecord.from_document(msg)

                case InputType.OSINT_ARTICLE:
                    msg = OsintArticleMessage.model_validate(payload)
                    return UnifiedInputRecord.from_osint(msg)

                case InputType.FINANCIAL_TRANSACTION:
                    msg = FinancialTransactionMessage.model_validate(payload)
                    return UnifiedInputRecord.from_financial(msg)

                case _:
                    logger.warning("unknown_topic", topic=topic)
                    return None

        except Exception as exc:
            logger.warning(
                "message_parse_failed",
                topic=topic,
                error=str(exc),
            )
            return None

    def poll_batch(
        self,
        max_records: int | None = None,
    ) -> list[UnifiedInputRecord]:
        """Poll for a batch of messages from all subscribed topics."""
        if self._consumer is None:
            raise KafkaConsumerError(
                "Consumer not connected. Call connect() first."
            )

        batch_size = max_records or self._config.max_poll_records
        records: list[UnifiedInputRecord] = []

        while len(records) < batch_size:
            msg = self._consumer.poll(timeout=1.0)

            if msg is None:
                break

            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    continue
                raise KafkaConsumerError(f"Kafka error: {msg.error()}")

            record = self._parse_message(msg.topic(), msg.value())
            if record:
                records.append(record)

        return records

    def poll_batch_by_type(
        self,
        max_records: int | None = None,
    ) -> dict[InputType, list[UnifiedInputRecord]]:
        """Poll and group records by input type for optimized batch processing."""
        records = self.poll_batch(max_records)

        grouped: dict[InputType, list[UnifiedInputRecord]] = {
            t: [] for t in InputType
        }

        for record in records:
            grouped[record.input_type].append(record)

        return grouped

    def commit(self) -> None:
        """Commit current offsets."""
        if self._consumer:
            self._consumer.commit(asynchronous=False)

    def close(self) -> None:
        """Close the consumer connection."""
        if self._consumer:
            self._consumer.close()
            self._consumer = None
            logger.info("kafka_consumer_closed")

    def __enter__(self) -> "KafkaMultiTopicConsumer":
        self.connect()
        return self

    def __exit__(self, *args) -> None:
        self.close()

    def stream(self) -> Iterator[dict[InputType, list[UnifiedInputRecord]]]:
        """Yield batches of records grouped by type continuously."""
        while True:
            batch = self.poll_batch_by_type()
            if any(batch.values()):
                yield batch
