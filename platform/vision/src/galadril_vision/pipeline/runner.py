"""Pipeline orchestrator driven by galadril-pipeline DAG."""

from __future__ import annotations

import time
import asyncio
from typing import TYPE_CHECKING, Any

import structlog

from galadril_vision.connectors.kafka.consumer import KafkaMultiTopicConsumer
from galadril_vision.connectors.postgres.client import PostgresClient
from galadril_vision.connectors.postgres.graph import GraphStore
from galadril_vision.connectors.postgres.vector import VectorStore

from galadril_inference import InferenceEngine, PredictionRequest
from galadril_inference.storage import S3Loader

if TYPE_CHECKING:
    from galadril_vision.common.config import VisionConfig
    from galadril_pipeline.graph import PipelineGraph

logger = structlog.get_logger(__name__)


class VisionPipeline:
    """Orchestrates dynamic pipeline execution."""

    def __init__(
        self, config: VisionConfig, pipeline_graph: PipelineGraph
    ) -> None:
        self._config = config
        self._graph = pipeline_graph
        self._kafka_consumer: KafkaMultiTopicConsumer | None = None
        self._pg_client: PostgresClient | None = None
        self._vector_store: VectorStore | None = None
        self._graph_store: GraphStore | None = None
        self._engine: InferenceEngine | None = None

        self._topic_to_sources: dict[str, list[str]] = {}
        for source in self._graph.config.sources:
            self._topic_to_sources.setdefault(source.topic, []).append(
                source.id
            )

    async def initialize(self) -> None:
        """Initialize connections and load models based on execution plan."""
        topics = self._graph.get_kafka_topics()
        self._kafka_consumer = KafkaMultiTopicConsumer(
            self._config.kafka,
            topics=topics,
            schema_registry_url=self._config.kafka.schema_registry,
        )
        self._kafka_consumer.connect()

        self._pg_client = PostgresClient(self._config.postgres)
        await self._pg_client.connect()

        self._vector_store = VectorStore(self._pg_client, self._config.postgres)
        await self._vector_store.initialize()

        self._graph_store = GraphStore(self._pg_client, self._config.postgres)
        await self._graph_store.initialize()

        loader = S3Loader(
            bucket=self._config.inference.bucket,
            prefix=self._config.inference.prefix,
            endpoint_url=self._config.inference.endpoint_url,
        )
        self._engine = InferenceEngine(loader=loader)

        execution_plan = self._graph.get_execution_plan()
        for step in execution_plan:
            if step.type == "inference" and step.model:
                model_name = step.model.split(".")[-1].lower()
                if "face_recognition" in model_name:
                    model_name = "face_recognition"

                try:
                    self._engine.load_model(model_name)
                    logger.info("model_preloaded", model=model_name)
                except Exception as exc:
                    logger.error(
                        "model_load_failed", model=model_name, error=str(exc)
                    )

        logger.info("vision_pipeline_initialized")

    async def shutdown(self) -> None:
        """Release resources."""
        if self._kafka_consumer:
            self._kafka_consumer.close()
        if self._pg_client:
            await self._pg_client.close()
        logger.info("vision_pipeline_shutdown")

    async def _execute_step(self, step_id: str, data: Any) -> Any:
        """Execute a single step for the data payload."""
        step = self._graph.get_step_by_id(step_id)

        if step.type == "inference" and self._engine:
            model_name = step.model.split(".")[-1].lower()
            if "face_recognition" in model_name:
                model_name = "face_recognition"

            action = (
                step.params.get("action", "embed") if step.params else "embed"
            )
            req = PredictionRequest(
                model_name=model_name,
                features={
                    "action": action,
                    "image": data.get("image")
                    if isinstance(data, dict)
                    else data,
                },
            )
            result = await asyncio.to_thread(self._engine.predict, req)
            return result.prediction

        return data

    async def _route_message(self, source_id: str, payload: Any) -> None:
        """Route a single message through the DAG."""
        next_steps = self._graph.get_outputs_for_step(source_id)
        queue = [(step_id, payload) for step_id in next_steps]

        while queue:
            step_id, data = queue.pop(0)
            try:
                result = await self._execute_step(step_id, data)
                further_steps = self._graph.get_outputs_for_step(step_id)

                if not further_steps:
                    logger.debug("pipeline_sink_reached", step_id=step_id)
                else:
                    for n_step in further_steps:
                        queue.append((n_step, result))
            except Exception as exc:
                logger.error(
                    "step_execution_failed", step_id=step_id, error=str(exc)
                )

    async def process_batch(
        self, batch: list[tuple[str, dict[str, Any]]]
    ) -> None:
        """Process a batch from Kafka."""
        start = time.perf_counter()

        for topic, payload in batch:
            sources = self._topic_to_sources.get(topic, [])
            for source_id in sources:
                await self._route_message(source_id, payload)

        elapsed_ms = (time.perf_counter() - start) * 1000
        logger.info(
            "batch_processed", size=len(batch), elapsed_ms=round(elapsed_ms, 2)
        )

    async def run(self) -> None:
        """Main loop consuming Kafka."""
        logger.info("vision_pipeline_started")
        if self._kafka_consumer is None:
            raise RuntimeError("Call await initialize() first.")

        try:
            for batch in self._kafka_consumer.stream():
                await self.process_batch(batch)
                self._kafka_consumer.commit()
        except KeyboardInterrupt:
            logger.info("pipeline_interrupted")
        finally:
            await self.shutdown()

    async def __aenter__(self) -> "VisionPipeline":
        await self.initialize()
        return self

    async def __aexit__(self, *args) -> None:
        await self.shutdown()
