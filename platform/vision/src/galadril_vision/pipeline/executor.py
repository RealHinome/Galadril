from __future__ import annotations

from typing import TYPE_CHECKING, Any
import structlog
import daft
from uuid import uuid4
from datetime import datetime, timezone

from common.types import (
    EmbeddingModality,
    EntityEmbedding,
    EntityStateRecord,
    EventRecord,
    EventType,
    GraphVertex,
)
from pipeline.transforms import download_images_udf, run_inference_udf

if TYPE_CHECKING:
    from galadril_pipeline.config import PipelineConfig
    from connectors.postgres.vector import VectorStore
    from connectors.postgres.graph import GraphStore
    from common.config import VisionConfig

logger = structlog.get_logger(__name__)


class ESKGPipelineExecutor:
    """Executes the pipeline."""

    def __init__(
        self,
        config: PipelineConfig,
        vision_config: VisionConfig,
        vector_store: VectorStore,
        graph_store: GraphStore,
    ) -> None:
        self.config = config
        self.vision_config = vision_config
        self._vector_store = vector_store
        self._graph_store = graph_store

    async def execute_batch(self, batch: list[dict[str, Any]]) -> None:
        """Process a batch through the DAG."""
        if not batch:
            return

        df = daft.from_pylist(batch)

        if "storage_path" in df.column_names:
            df = df.with_column(
                "image_data",
                download_images_udf(
                    df["storage_path"],
                    df["record_id"],
                    bucket=self.vision_config.image_store.bucket,
                    prefix=self.vision_config.image_store.prefix,
                    endpoint_url=self.vision_config.image_store.endpoint_url,
                ),
            )

        for step in self.config.pipeline:
            if step.type == "inference":
                model_name = step.model.split(".")[-1].lower()
                action = (
                    step.params.get("action", "embed")
                    if step.params
                    else "embed"
                )
                df = df.with_column(
                    f"{step.step}_result",
                    run_inference_udf(
                        df["image_data"],
                        df["record_id"],
                        artifact_bucket=self.vision_config.inference.bucket,
                        artifact_prefix=self.vision_config.inference.prefix,
                        artifact_endpoint_url=self.vision_config.inference.endpoint_url,
                        model_name=model_name,
                        action=action,
                    ),
                )

        computed_records = df.to_pylist()

        for record in computed_records:
            await self._process_eskg_logic(record)

    async def _process_eskg_logic(self, record: dict[str, Any]) -> None:
        """Execute resolving and sinking sequentially per record."""
        for step in self.config.pipeline:
            if step.type == "resolve":
                input_col = f"{step.input_from[0]}_result"
                inference_data = record.get(input_col)
                if not inference_data or inference_data.get("error"):
                    continue

                modality = (
                    step.params.get("modality", "face")
                    if step.params
                    else "face"
                )
                threshold = (
                    step.params.get("threshold", 0.8) if step.params else 0.8
                )
                items = inference_data.get("prediction", {}).get("faces", [])

                for item in items:
                    vector = item.get("embedding")
                    if vector:
                        matches = await self._vector_store.find_similar(
                            embedding=vector,
                            modality=EmbeddingModality(modality),
                            top_k=1,
                        )
                        if matches and matches[0][1] >= threshold:
                            item["resolved_entity_id"] = matches[0][0]
                            item["is_unknown"] = False
                        else:
                            item["resolved_entity_id"] = (
                                f"unknown_{modality}_{uuid4().hex}"
                            )
                            item["is_unknown"] = True
                record[f"{step.step}_resolved"] = items

            elif step.type == "sink":
                input_data = record.get(f"{step.input_from[0]}_resolved", [])

                event = EventRecord(
                    event_id=f"evt_{record['record_id']}",
                    event_type=EventType.OBSERVATION,
                    properties={"source": record.get("source", "unknown")},
                    timestamp=datetime.now(timezone.utc),
                )
                await self._graph_store.insert_event(event)

                for item in input_data:
                    entity_id = item.get("resolved_entity_id")
                    if not entity_id:
                        continue

                    entity_type = (
                        step.params.get("entity_type", "PERSON")
                        if step.params
                        else "PERSON"
                    )
                    modality = (
                        step.params.get("modality", "face")
                        if step.params
                        else "face"
                    )

                    await self._graph_store.ensure_vertex(
                        GraphVertex(
                            vertex_id=entity_id,
                            label=entity_type,
                            properties={
                                "is_unknown": item.get("is_unknown", True)
                            },
                        )
                    )
                    await self._graph_store.link_entity_to_event(
                        entity_id=entity_id,
                        event_id=event.event_id,
                        role="APPEARS_IN",
                    )

                    # 2. Update TimescaleDB States
                    state = EntityStateRecord(
                        entity_id=entity_id,
                        event_id=event.event_id,
                        state_type="sighting",
                        state_value={
                            "confidence": item.get("confidence", 0.0),
                            "bbox": item.get("bbox"),
                        },
                        event_time=event.timestamp,
                    )
                    await self._graph_store.insert_entity_state(state)

                    # 3. Store new Embedding vector
                    if item.get("embedding"):
                        emb_record = EntityEmbedding(
                            modality=EmbeddingModality(modality),
                            vector=item.get("embedding"),
                            metadata={"event_id": event.event_id},
                        )
                        await self._vector_store.store_embedding(
                            emb_record, entity_id
                        )
