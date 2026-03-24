from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING

import orjson
import structlog
from pgvector.psycopg import register_vector_async
from psycopg import sql

from common.exceptions import VectorSearchError
from common.types import DetectedFaceRecord

if TYPE_CHECKING:
    from common.config import PostgresConfig
    from connectors.postgres.client import PostgresClient

logger = structlog.get_logger(__name__)

_TABLE_INIT_SQL = """
CREATE TABLE IF NOT EXISTS face_embeddings (
    id TEXT,
    person_id TEXT NOT NULL,
    embedding vector({dimensions}),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB DEFAULT '{{}}'::jsonb,
    PRIMARY KEY (id, created_at)
);

SELECT create_hypertable(
    'face_embeddings',
    'created_at',
    if_not_exists => TRUE,
    migrate_data => TRUE
);

CREATE INDEX IF NOT EXISTS idx_face_embeddings
ON face_embeddings
USING diskann (embedding)
WITH (storage_layout = 'memory_optimized');
"""


class VectorStore:
    """Face embedding storage and similarity search using pgvectorscale."""

    def __init__(self, client: PostgresClient, config: PostgresConfig) -> None:
        self._client = client
        self._config = config

    async def initialize(self) -> None:
        """Create the embeddings table and index."""
        async with self._client.connection() as conn:
            await register_vector_async(conn)
            query = sql.SQL(_TABLE_INIT_SQL).format(
                dimensions=sql.Literal(self._config.vector_dimensions)
            )
            await conn.execute(query)
        logger.info("vector_store_initialized")

    async def find_similar(
        self,
        embedding: list[float],
        top_k: int = 5,
    ) -> list[tuple[str, float]]:
        """Find the most similar face embeddings."""
        async with self._client.connection() as conn:
            await register_vector_async(conn)

            query = sql.SQL("""
                SELECT person_id, similarity
                FROM (
                    SELECT
                        person_id,
                        1 - (embedding <=> $1::vector) AS similarity,
                        embedding <=> $1::vector AS distance
                    FROM face_embeddings
                    ORDER BY distance
                    LIMIT $3
                ) AS sub
                WHERE similarity >= $2;
            """)

            result = await conn.execute(
                query,
                (embedding, self._config.similarity_threshold, top_k),
            )

            rows = await result.fetchall()
            return [(str(row[0]), float(row[1])) for row in rows]

    async def identify_face(
        self,
        face: DetectedFaceRecord,
    ) -> DetectedFaceRecord:
        """Attempt to identify a face by finding similar embeddings."""
        if not face.embedding:
            return face

        try:
            matches = await self.find_similar(face.embedding, top_k=1)

            if matches:
                person_id, confidence = matches[0]
                face.identified_person_id = person_id
                face.identification_confidence = confidence
                face.is_unknown = False

                logger.debug(
                    "face_identified",
                    face_id=face.face_id,
                    person_id=person_id,
                    confidence=confidence,
                )
            else:
                face.is_unknown = True

        except Exception as exc:
            raise VectorSearchError(f"Identification failed: {exc}") from exc

        return face

    async def store_embedding(
        self,
        face: DetectedFaceRecord,
        person_id: str,
    ) -> None:
        """Store a new face embedding for future identification."""
        async with self._client.connection() as conn:
            await register_vector_async(conn)

            query = sql.SQL("""
                INSERT INTO face_embeddings (id, person_id, embedding, metadata, created_at)
                VALUES ($1, $2, $3::vector, $4, $5)
            """)

            metadata_json = orjson.dumps(
                {"image_id": face.image_id, "bbox": face.bbox}
            ).decode()

            await conn.execute(
                query,
                (
                    face.face_id,
                    person_id,
                    face.embedding,
                    metadata_json,
                    datetime.now(timezone.utc),
                ),
            )

        logger.info(
            "embedding_stored",
            face_id=face.face_id,
            person_id=person_id,
        )
