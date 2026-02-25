"""Graph operations."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from datetime import datetime

import structlog
import orjson

from galadril_vision.common.exceptions import GraphOperationError
from galadril_vision.common.types import DetectedFaceRecord, GraphEdge

if TYPE_CHECKING:
    from galadril_vision.config import PostgresConfig
    from galadril_vision.connectors.postgres.client import PostgresClient

logger = structlog.get_logger(__name__)


class GraphStore:
    """Apache AGE graph operations for person relationships."""

    def __init__(self, client: PostgresClient, config: PostgresConfig) -> None:
        self._client = client
        self._config = config
        self._graph_name = config.graph_name

    async def initialize(self) -> None:
        async with self._client.connection() as conn:
            await conn.execute("LOAD 'age'")
            await conn.execute("SET search_path = ag_catalog, public")
            await conn.execute(
                f"""
                SELECT *
                FROM cypher(
                    '{self._graph_name}',
                    $$
                        CREATE CONSTRAINT IF NOT EXISTS
                        FOR (p:Person)
                        REQUIRE p.id IS UNIQUE
                    $$
                ) AS (result agtype);
                """
            )

        logger.info("graph_store_initialized", graph=self._graph_name)

    async def ensure_person_vertex(
        self,
        person_id: str,
        properties: dict[str, Any] | None = None,
    ) -> None:
        params = {
            "person_id": person_id,
            "props": properties or {},
        }

        try:
            async with self._client.connection() as conn:
                query = f"""
                    SELECT *
                    FROM cypher(
                        '{self._graph_name}',
                        $$
                            MERGE (p:Person {{id: person_id}})
                            ON CREATE SET p += props
                            RETURN p
                        $$,
                        %s::agtype
                    ) AS (p agtype);
                """
                await conn.execute(query, orjson.dumps(params))

            logger.debug("person_vertex_ensured", person_id=person_id)

        except Exception as exc:
            raise GraphOperationError("ensure_person_vertex", str(exc)) from exc

    async def create_relationship(self, edge: GraphEdge) -> None:
        if edge.edge_type != "APPEARS_WITH":
            raise GraphOperationError(
                "create_relationship", "invalid edge type"
            )

        params = {
            "source_id": edge.source_vertex_id,
            "target_id": edge.target_vertex_id,
            "props": edge.properties,
            "detected_at": datetime.utcnow().isoformat(),
        }

        try:
            async with self._client.connection() as conn:
                query = f"""
                    SELECT *
                    FROM cypher(
                        '{self._graph_name}',
                        $$
                            MATCH (a:Person {{id: source_id}})
                            MATCH (b:Person {{id: target_id}})
                            MERGE (a)-[r:APPEARS_WITH]->(b)
                            ON CREATE SET r += props
                            SET r.detected_at = detected_at
                            RETURN r
                        $$,
                        %s::agtype
                    ) AS (r agtype);
                """

                await conn.execute(query, orjson.dumps(params))

            logger.debug(
                "relationship_created",
                source=edge.source_vertex_id,
                target=edge.target_vertex_id,
                edge_type=edge.edge_type,
            )

        except Exception as exc:
            raise GraphOperationError("create_relationship", str(exc)) from exc

    async def link_faces_from_image(
        self,
        image_id: str,
        faces: list[DetectedFaceRecord],
        unknown_prefix: str,
    ) -> list[GraphEdge]:
        edges_created: list[GraphEdge] = []
        vertex_ids: list[str] = []

        # TODO: N+1 problem, we should batch.
        for face in faces:
            if face.is_unknown:
                vertex_id = f"{unknown_prefix}_{face.face_id}"
                props = {"first_seen_image": image_id, "type": "unknown"}
            else:
                vertex_id = face.identified_person_id
                props = {"type": "known"}

            await self.ensure_person_vertex(vertex_id, props)
            vertex_ids.append(vertex_id)

        for i, source_id in enumerate(vertex_ids):
            for target_id in vertex_ids[i + 1 :]:
                edge = GraphEdge(
                    source_vertex_id=source_id,
                    target_vertex_id=target_id,
                    edge_type="APPEARS_WITH",
                    properties={
                        "image_id": image_id,
                    },
                )
                await self.create_relationship(edge)
                edges_created.append(edge)

        logger.info(
            "image_faces_linked",
            image_id=image_id,
            faces_count=len(faces),
            edges_created=len(edges_created),
        )

        return edges_created
