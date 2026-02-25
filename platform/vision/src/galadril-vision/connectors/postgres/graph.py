"""Apache AGE graph operations for multi-entity relationships."""

from __future__ import annotations
from datetime import datetime
from typing import TYPE_CHECKING, Any

import structlog

from galadril_vision.common.exceptions import GraphOperationError
from galadril_vision.common.types import (
    DetectedFaceRecord,
    EntityType,
    ExtractedEntity,
    GraphEdge,
    GraphVertex,
)

if TYPE_CHECKING:
    from galadril_vision.config import PostgresConfig
    from galadril_vision.connectors.postgres.client import PostgresClient

logger = structlog.get_logger(__name__)


class GraphStore:
    """Apache AGE graph operations for multi-entity relationships."""

    def __init__(self, client: PostgresClient, config: PostgresConfig) -> None:
        self._client = client
        self._config = config
        self._graph_name = config.graph_name

    async def initialize(self) -> None:
        """Ensure the graph exists and search path is set."""
        async with self._client.connection() as conn:
            await conn.execute("LOAD 'age'")
            await conn.execute("SET search_path = ag_catalog, public")
            await conn.execute(
                f"""
                DO $$
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM ag_catalog.ag_graph WHERE name = '{self._graph_name}'
                    ) THEN
                        PERFORM ag_catalog.create_graph('{self._graph_name}');
                    END IF;
                END $$;
                """
            )
        logger.info("graph_store_initialized", graph=self._graph_name)

    async def ensure_vertex(self, vertex: GraphVertex) -> None:
        """Create or update a vertex."""
        props = vertex.properties.copy()
        props["id"] = vertex.vertex_id
        props_cypher = ", ".join(f"{k}: {self._cypher_value(v)}" for k, v in props.items())

        try:
            async with self._client.connection() as conn:
                await conn.execute("LOAD 'age'")
                await conn.execute("SET search_path = ag_catalog, public")
                await conn.execute(
                    f"""
                    SELECT * FROM cypher('{self._graph_name}', $$
                        MERGE (v:{vertex.label.value} {{{props_cypher}}})
                        RETURN v
                    $$) AS (v agtype)
                    """
                )
            logger.debug("vertex_ensured", vertex_id=vertex.vertex_id, label=vertex.label)
        except Exception as exc:
            raise GraphOperationError("ensure_vertex", str(exc)) from exc

    async def create_edge(self, edge: GraphEdge) -> None:
        """Create an edge between two vertices."""
        props_cypher = ", ".join(f"{k}: {self._cypher_value(v)}" for k, v in edge.properties.items())
        props_str = f"{{{props_cypher}}}" if props_cypher else ""

        try:
            async with self._client.connection() as conn:
                await conn.execute("LOAD 'age'")
                await conn.execute("SET search_path = ag_catalog, public")
                await conn.execute(
                    f"""
                    SELECT * FROM cypher('{self._graph_name}', $$
                        MATCH (a {{id: '{edge.source_vertex_id}'}})
                        MATCH (b {{id: '{edge.target_vertex_id}'}})
                        MERGE (a)-[r:{edge.edge_type} {props_str}]->(b)
                        RETURN r
                    $$) AS (r agtype)
                    """
                )
            logger.debug(
                "edge_created",
                source=edge.source_vertex_id,
                target=edge.target_vertex_id,
                edge_type=edge.edge_type,
            )
        except Exception as exc:
            raise GraphOperationError("create_edge", str(exc)) from exc

    async def create_transaction_edge(
        self,
        sender_id: str,
        receiver_id: str,
        amount: float,
        currency: str,
        transaction_id: str,
        timestamp: datetime,
    ) -> None:
        """Create vertices and edge for a financial transaction."""
        await self.ensure_vertex(
            GraphVertex(vertex_id=sender_id, label=EntityType.ACCOUNT, properties={"account_id": sender_id})
        )
        await self.ensure_vertex(
            GraphVertex(vertex_id=receiver_id, label=EntityType.ACCOUNT, properties={"account_id": receiver_id})
        )
        await self.create_edge(
            GraphEdge(
                source_vertex_id=sender_id,
                target_vertex_id=receiver_id,
                edge_type="TRANSACTED_WITH",
                properties={
                    "transaction_id": transaction_id,
                    "amount": amount,
                    "currency": currency,
                    "timestamp": timestamp.isoformat(),
                },
            )
        )
        logger.info(
            "transaction_edge_created",
            sender=sender_id,
            receiver=receiver_id,
            amount=amount,
            currency=currency,
        )

    async def link_faces_from_image(
        self,
        image_id: str,
        faces: list[DetectedFaceRecord],
        unknown_prefix: str,
    ) -> list[GraphEdge]:
        """Create APPEARS_WITH relationships between faces in an image."""
        edges_created: list[GraphEdge] = []
        vertex_ids: list[str] = []

        for face in faces:
            if face.is_unknown:
                vertex_id = f"{unknown_prefix}_{face.face_id}"
                props = {"first_seen_image": image_id, "type": "unknown"}
            else:
                vertex_id = face.identified_person_id
                props = {"type": "known"}

            await self.ensure_vertex(GraphVertex(vertex_id=vertex_id, label=EntityType.PERSON, properties=props))
            vertex_ids.append(vertex_id)

        for i, source_id in enumerate(vertex_ids):
            for target_id in vertex_ids[i + 1:]:
                edge = GraphEdge(
                    source_vertex_id=source_id,
                    target_vertex_id=target_id,
                    edge_type="APPEARS_WITH",
                    properties={"image_id": image_id},
                )
                await self.create_edge(edge)
                edges_created.append(edge)

        logger.info(
            "image_faces_linked",
            image_id=image_id,
            faces_count=len(faces),
            edges_created=len(edges_created),
        )
        return edges_created

    async def link_entities_from_article(
        self,
        article_id: str,
        entities: list[ExtractedEntity],
    ) -> list[GraphEdge]:
        """Create MENTIONED_WITH relationships between entities in an article."""
        edges_created: list[GraphEdge] = []

        for entity in entities:
            vertex_id = entity.resolved_id or f"entity_{entity.entity_id}"
            await self.ensure_vertex(
                GraphVertex(
                    vertex_id=vertex_id,
                    label=EntityType(entity.entity_type),
                    properties={"name": entity.name, **entity.properties},
                )
            )

        vertex_ids = [e.resolved_id or f"entity_{e.entity_id}" for e in entities]
        for i, source_id in enumerate(vertex_ids):
            for j, target_id in enumerate(vertex_ids[i + 1:], start=i + 1):
                edge = GraphEdge(
                    source_vertex_id=source_id,
                    target_vertex_id=target_id,
                    edge_type="MENTIONED_WITH",
                    properties={
                        "article_id": article_id,
                        "source_type": entities[i].entity_type,
                        "target_type": entities[j].entity_type,
                    },
                )
                await self.create_edge(edge)
                edges_created.append(edge)

        return edges_created

    @staticmethod
    def _cypher_value(value: Any) -> str:
        """Convert Python value to Cypher literal."""
        if isinstance(value, str):
            escaped = value.replace("'", "\\'")
            return f"'{escaped}'"
        if isinstance(value, bool):
            return "true" if value else "false"
        if isinstance(value, (int, float)):
            return str(value)
        if value is None:
            return "null"
        return f"'{value}'"
