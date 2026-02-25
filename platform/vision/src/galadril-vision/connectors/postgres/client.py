"""PostgreSQL client."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, AsyncIterator

import structlog
from psycopg import AsyncConnection
from psycopg_pool import AsyncConnectionPool

if TYPE_CHECKING:
    from galadril_vision.config import PostgresConfig

logger = structlog.get_logger(__name__)


class PostgresClient:
    """Async PostgreSQL client with connection pooling."""

    def __init__(self, config: PostgresConfig) -> None:
        self._config = config
        self._pool: AsyncConnectionPool | None = None

    async def connect(self) -> None:
        """Initialize the connection pool."""
        self._pool = AsyncConnectionPool(
            conninfo=str(self._config.dsn),
            min_size=self._config.min_connections,
            max_size=self._config.max_connections,
            open=False,
        )
        await self._pool.open()

        async with self.connection() as conn:
            await self._init_extensions(conn)

        logger.info(
            "postgres_pool_initialized",
            min_size=self._config.min_connections,
            max_size=self._config.max_connections,
        )

    async def _init_extensions(self, conn: AsyncConnection) -> None:
        """Ensure required PostgreSQL extensions are loaded."""
        await conn.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        await conn.execute("CREATE EXTENSION IF NOT EXISTS age;")
        await conn.execute("CREATE EXTENSION IF NOT EXISTS timescaledb;")

        # Load AGE extension.
        # This is already done on galadril-database.
        await conn.execute("LOAD 'age';")
        await conn.execute("SET search_path = ag_catalog, public, '$user';")

        # Create graph if not exists.
        graph_name = self._config.graph_name
        await conn.execute(
            f"""
            SELECT * FROM ag_catalog.create_graph('{graph_name}')
            WHERE NOT EXISTS (
                SELECT 1 FROM ag_catalog.ag_graph WHERE name = '{graph_name}'
            )
            """
        )

        logger.info("postgres_extensions_initialized", graph=graph_name)

    @asynccontextmanager
    async def connection(self) -> AsyncIterator[AsyncConnection]:
        """Get a connection from the pool."""
        if self._pool is None:
            raise RuntimeError("Pool not initialized. Call connect() first.")

        async with self._pool.connection() as conn:
            yield conn

    async def close(self) -> None:
        """Close the connection pool."""
        if self._pool:
            await self._pool.close()
            self._pool = None
            logger.info("postgres_pool_closed")

    async def __aenter__(self) -> "PostgresClient":
        await self.connect()
        return self

    async def __aexit__(self, *args) -> None:
        await self.close()
