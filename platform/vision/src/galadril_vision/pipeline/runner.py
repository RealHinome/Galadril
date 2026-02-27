"""Main Daft + Ray pipeline orchestrator."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

import daft
import ray
import structlog
from daft import col

from galadril_vision.common.types import (
    DetectedFaceRecord,
    ProcessedRecord,
    ProcessingStatus,
)
from galadril_vision.connectors.kafka.consumer import KafkaMultiTopicConsumer
from galadril_vision.connectors.kafka.schemas import (
    InputType,
    UnifiedInputRecord,
)
from galadril_vision.connectors.postgres.client import PostgresClient
from galadril_vision.connectors.postgres.graph import GraphStore
from galadril_vision.connectors.postgres.vector import VectorStore
from galadril_vision.pipeline.transforms import (
    download_images_udf,
    run_inference_udf,
)

if TYPE_CHECKING:
    from galadril_vision.common.config import VisionConfig

logger = structlog.get_logger(__name__)


class VisionPipeline:
    """Orchestrates heterogeneous input processing using Daft + Ray."""

    def __init__(self, config: VisionConfig) -> None:
        self._config = config
        self._kafka_consumer: KafkaMultiTopicConsumer | None = None
        self._pg_client: PostgresClient | None = None
        self._vector_store: VectorStore | None = None
        self._graph_store: GraphStore | None = None

    async def initialize(self) -> None:
        """Initialize all connections and the Ray cluster."""
        ray_config = self._config.ray
        ray.init(
            address=ray_config.address,
            num_cpus=ray_config.num_cpus,
            num_gpus=ray_config.num_gpus,
        )
        self._kafka_consumer = KafkaMultiTopicConsumer(
            self._config.kafka,
            schema_registry_url=self._config.kafka.schema_registry,
        )
        self._kafka_consumer.connect()

        self._pg_client = PostgresClient(self._config.postgres)
        await self._pg_client.connect()

        self._vector_store = VectorStore(self._pg_client, self._config.postgres)
        await self._vector_store.initialize()

        self._graph_store = GraphStore(self._pg_client, self._config.postgres)
        await self._graph_store.initialize()

        logger.info("vision_pipeline_initialized")

    async def shutdown(self) -> None:
        """Release all resources."""
        if self._kafka_consumer:
            self._kafka_consumer.close()
        if self._pg_client:
            await self._pg_client.close()
        ray.shutdown()
        logger.info("vision_pipeline_shutdown")

    def _process_images(
        self,
        records: list[UnifiedInputRecord],
    ) -> dict[str, list]:
        """Build a Daft pipeline for image download + inference."""
        if not records:
            return {"record_id": [], "inference": []}

        img_cfg = self._config.image_store
        inf_cfg = self._config.inference

        df = daft.from_pydict(
            {
                "record_id": [r.record_id for r in records],
                "storage_path": [r.storage_path for r in records],
                "input_type": [r.input_type.value for r in records],
            }
        )

        df = df.with_column(
            "image",
            download_images_udf(
                col("storage_path"),
                col("record_id"),
                bucket=img_cfg.bucket,
                prefix=img_cfg.prefix,
                endpoint_url=img_cfg.endpoint_url,
            ),
        )

        df = df.with_column(
            "inference",
            run_inference_udf(
                col("image"),
                col("record_id"),
                artifact_bucket=inf_cfg.bucket,
                artifact_prefix=inf_cfg.prefix,
                artifact_endpoint_url=inf_cfg.endpoint_url,
                model_name=self._config.face_model_name,
            ),
        )

        result = df.select("record_id", "inference").collect()
        return result.to_pydict()

    async def _identify_faces(
        self,
        daft_results: dict[str, list],
    ) -> list[ProcessedRecord]:
        """Post-process inference results: identify faces and link in graph."""
        processed: list[ProcessedRecord] = []

        for record_id, inference in zip(
            daft_results["record_id"],
            daft_results["inference"],
        ):
            faces_data = inference.get("faces", [])
            error = inference.get("error")

            if error:
                processed.append(
                    ProcessedRecord(
                        record_id=record_id,
                        input_type=InputType.SATELLITE_IMAGE.value,
                        status=ProcessingStatus.FAILED,
                        error=error,
                    )
                )
                continue

            if self._vector_store is None or self._graph_store is None:
                raise RuntimeError(
                    "Pipeline components not initialized. Did you call initialize()?"
                )

            face_records: list[DetectedFaceRecord] = []
            for i, face in enumerate(faces_data):
                face_records.append(
                    DetectedFaceRecord(
                        face_id=f"{record_id}_{i}",
                        image_id=record_id,
                        bbox=face.get("bbox", []),
                        confidence=face.get("confidence", 0.0),
                        embedding=face.get("embedding", []),
                    )
                )

            # Identify each face via pgvectorscale similarity search.
            for face in face_records:
                await self._vector_store.identify_face(face)

            await self._graph_store.link_faces_from_image(
                image_id=record_id,
                faces=face_records,
                unknown_prefix=self._config.unknown_vertex_prefix,
            )

            processed.append(
                ProcessedRecord(
                    record_id=record_id,
                    input_type=InputType.SATELLITE_IMAGE.value,
                    status=ProcessingStatus.STORED,
                    faces=face_records,
                    processing_time_ms=inference.get(
                        "inference_latency_ms", 0.0
                    ),
                )
            )

        return processed

    def _process_text(
        self,
        records: list[UnifiedInputRecord],
    ) -> dict[str, list]:
        """Extract entities from OSINT text via Daft + Ray."""
        return {}

    async def _link_text_entities(
        self,
        daft_results: dict[str, list],
    ) -> list[ProcessedRecord]:
        """Create graph relationships for text-extracted entities."""
        processed: list[ProcessedRecord] = []
        return processed

    async def _process_financial(
        self,
        records: list[UnifiedInputRecord],
    ) -> list[ProcessedRecord]:
        """Process financial transactions — account linking only."""
        processed: list[ProcessedRecord] = []
        return processed

    async def process_batch(
        self,
        grouped: dict[InputType, list[UnifiedInputRecord]],
    ) -> list[ProcessedRecord]:
        """Process a heterogeneous batch of records."""
        start = time.perf_counter()
        all_processed: list[ProcessedRecord] = []

        image_records = grouped.get(InputType.SATELLITE_IMAGE, []) + [
            r for r in grouped.get(InputType.DOCUMENT, []) if r.is_image
        ]
        if image_records:
            daft_results = self._process_images(image_records)
            all_processed.extend(await self._identify_faces(daft_results))

        osint_records = grouped.get(InputType.OSINT_ARTICLE, [])
        if osint_records:
            daft_results = self._process_text(osint_records)
            all_processed.extend(await self._link_text_entities(daft_results))

        financial_records = grouped.get(InputType.FINANCIAL_TRANSACTION, [])
        if financial_records:
            all_processed.extend(
                await self._process_financial(financial_records)
            )

        doc_records = [
            r for r in grouped.get(InputType.DOCUMENT, []) if not r.is_image
        ]
        for r in doc_records:
            all_processed.append(
                ProcessedRecord(
                    record_id=r.record_id,
                    input_type=r.input_type.value,
                    status=ProcessingStatus.SKIPPED,
                )
            )

        elapsed_ms = (time.perf_counter() - start) * 1000
        logger.info(
            "batch_processed",
            images=len(image_records),
            osint=len(osint_records),
            financial=len(financial_records),
            skipped_docs=len(doc_records),
            elapsed_ms=round(elapsed_ms, 2),
        )

        return all_processed

    async def run(self) -> None:
        """Consume from Kafka and process continuously."""
        logger.info("vision_pipeline_started")

        if self._kafka_consumer is None:
            raise RuntimeError(
                "Pipeline components not initialized. Did you call await initialize()?"
            )

        try:
            for grouped_batch in self._kafka_consumer.stream():
                try:
                    processed = await self.process_batch(grouped_batch)
                    self._kafka_consumer.commit()

                    stored = sum(
                        1
                        for p in processed
                        if p.status == ProcessingStatus.STORED
                    )
                    logger.info(
                        "batch_committed",
                        total=len(processed),
                        stored=stored,
                    )

                except Exception as exc:
                    logger.exception("batch_failed", error=str(exc))

        except KeyboardInterrupt:
            logger.info("pipeline_interrupted")
        finally:
            await self.shutdown()

    async def __aenter__(self) -> "VisionPipeline":
        await self.initialize()
        return self

    async def __aexit__(self, *args) -> None:
        await self.shutdown()
