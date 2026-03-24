"""Kafka connector module."""

from connectors.kafka.consumer import KafkaMultiTopicConsumer
from connectors.kafka.schemas import (
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
