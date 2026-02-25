"""pgvectorscale operations."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog
import orjson
from pgvector.psycopg import register_vector_async
from datetime import datetime, timezone

from galadril_vision.common.exceptions import VectorSearchError
from galadril_vision.common.types import DetectedFaceRecord

if TYPE_CHECKING:
    from galadril_vision.config import PostgresConfig
    from galadril_vision.connectors.postgres.client import PostgresClient

logger = structlog.get_logger(__name__)

# TODO: Use .sql files.
_TABLE_INIT_SQL = """
CREATE TABLE IF NOT EXISTS face_embeddings (
    id TEXT,
    person_id TEXT NOT NULL,
    embedding vector({dimensions}),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb,
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
            await conn.execute(
                _TABLE_INIT_SQL.format(
                    dimensions=self._config.vector_dimensions
                )
            )
        logger.info("vector_store_initialized")

    async def find_similar(
        self,
        embedding: list[float],
        top_k: int = 5,
    ) -> list[tuple[str, float]]:
        """Find the most similar face embeddings.

        Returns:
            List of (person_id, similarity_score) tuples, ordered by similarity.
        """
        async with self._client.connection() as conn:
            await register_vector_async(conn)

            result = await conn.execute(
                """
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
                """,
                (embedding, self._config.similarity_threshold, top_k),
            )

            rows = await result.fetchall()
            return [(row[0], row[1]) for row in rows]

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

            await conn.execute(
                """
                INSERT INTO face_embeddings (id, person_id, embedding, metadata, created_at)
                VALUES ($1, $2, $3::vector, $4, $5)
                """,
                (
                    face.face_id,
                    person_id,
                    face.embedding,
                    orjson.dumps(
                        {"image_id": face.image_id, "bbox": face.bbox}
                    ),
                    datetime.now(timezone.utc),
                ),
            )

        logger.info(
            "embedding_stored",
            face_id=face.face_id,
            person_id=person_id,
        )
