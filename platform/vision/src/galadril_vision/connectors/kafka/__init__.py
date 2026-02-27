"""Kafka connector module."""

from galadril_vision.connectors.kafka.consumer import KafkaMultiTopicConsumer
from galadril_vision.connectors.kafka.schemas import (
    SatelliteImageMessage,
    UnifiedInputRecord,
    DocumentMessage,
    OsintArticleMessage,
    FinancialTransactionMessage,
)

__all__ = [
    "KafkaMultiTopicConsumer",
    "SatelliteImageMessage",
    "DocumentMessage",
    "OsintArticleMessage",
    "FinancialTransactionMessage",
    "UnifiedInputRecord",
]
