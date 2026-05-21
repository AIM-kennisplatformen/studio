from datetime import UTC, datetime
from typing import Any, Literal
from uuid import UUID, uuid4

import asyncpg
from loguru import logger

from backend.models.session import Session, SessionMessage


DEFAULT_SESSION_NAME = "New session"


class PostgresStore:
    def __init__(self) -> None:
        self.pool: asyncpg.Pool | None = None

    async def connect(self, config_dict: dict) -> None:
        if self.pool is not None:
            return

        url = config_dict["postgres_url"]
        self.pool = await asyncpg.create_pool(url)
        await self._init_schema()
        logger.info(f"✓ Connected to Postgres at {url}")

    async def close(self) -> None:
        if self.pool is None:
            return

        await self.pool.close()
        self.pool = None
        logger.info("✓ Closed Postgres connection")

    def _ensure_connected(self) -> None:
        if self.pool is None:
            raise RuntimeError(
                f"{self.__class__.__name__} used before connect() was called"
            )

    async def _init_schema(self) -> None:
        self._ensure_connected()
        assert self.pool is not None

        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id UUID PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    updated_at TIMESTAMPTZ NOT NULL
                )
                """
            )
            await conn.execute(
                """
                CREATE INDEX IF NOT EXISTS sessions_user_updated_idx
                ON sessions (user_id, updated_at DESC)
                """
            )
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS session_messages (
                    message_id UUID PRIMARY KEY,
                    session_id UUID NOT NULL REFERENCES sessions(session_id)
                        ON DELETE CASCADE,
                    role TEXT NOT NULL CHECK (role IN ('ai', 'user')),
                    content TEXT NOT NULL,
                    created_at TIMESTAMPTZ NOT NULL,
                    updated_at TIMESTAMPTZ NOT NULL
                )
                """
            )
            await conn.execute(
                """
                CREATE INDEX IF NOT EXISTS session_messages_session_created_idx
                ON session_messages (session_id, created_at ASC)
                """
            )

    @staticmethod
    def _row_to_session(row: Any) -> Session:
        return Session(
            session_id=row["session_id"],
            user_id=row["user_id"],
            name=row["name"],
            updated_at=row["updated_at"],
        )

    @staticmethod
    def _row_to_message(row: Any) -> SessionMessage:
        return SessionMessage(
            message_id=row["message_id"],
            role=row["role"],
            content=row["content"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    async def create_session(
        self,
        user_id: str,
        name: str = DEFAULT_SESSION_NAME,
    ) -> Session:
        self._ensure_connected()
        assert self.pool is not None

        session_id = uuid4()
        now = datetime.now(UTC)
        row = await self.pool.fetchrow(
            """
            INSERT INTO sessions (session_id, user_id, name, updated_at)
            VALUES ($1, $2, $3, $4)
            RETURNING session_id, user_id, name, updated_at
            """,
            session_id,
            user_id,
            name,
            now,
        )
        return self._row_to_session(row)

    async def list_sessions(self, user_id: str) -> list[Session]:
        self._ensure_connected()
        assert self.pool is not None

        rows = await self.pool.fetch(
            """
            SELECT session_id, user_id, name, updated_at
            FROM sessions
            WHERE user_id = $1
            ORDER BY updated_at DESC
            """,
            user_id,
        )
        return [self._row_to_session(row) for row in rows]

    async def get_latest_session(self, user_id: str) -> Session | None:
        self._ensure_connected()
        assert self.pool is not None

        row = await self.pool.fetchrow(
            """
            SELECT session_id, user_id, name, updated_at
            FROM sessions
            WHERE user_id = $1
            ORDER BY updated_at DESC
            LIMIT 1
            """,
            user_id,
        )
        return self._row_to_session(row) if row else None

    async def get_session(self, user_id: str, session_id: UUID) -> Session | None:
        self._ensure_connected()
        assert self.pool is not None

        row = await self.pool.fetchrow(
            """
            SELECT session_id, user_id, name, updated_at
            FROM sessions
            WHERE user_id = $1 AND session_id = $2
            """,
            user_id,
            session_id,
        )
        return self._row_to_session(row) if row else None

    async def update_session_name(
        self,
        user_id: str,
        session_id: UUID,
        name: str,
        current_name: str | None = DEFAULT_SESSION_NAME,
    ) -> Session | None:
        self._ensure_connected()
        assert self.pool is not None

        if current_name is None:
            row = await self.pool.fetchrow(
                """
                UPDATE sessions
                SET name = $3
                WHERE user_id = $1 AND session_id = $2
                RETURNING session_id, user_id, name, updated_at
                """,
                user_id,
                session_id,
                name,
            )
        else:
            row = await self.pool.fetchrow(
                """
                UPDATE sessions
                SET name = $4
                WHERE user_id = $1 AND session_id = $2 AND name = $3
                RETURNING session_id, user_id, name, updated_at
                """,
                user_id,
                session_id,
                current_name,
                name,
            )
        return self._row_to_session(row) if row else None

    async def add_message(
        self,
        user_id: str,
        session_id: UUID,
        role: Literal["ai", "user"],
        content: str,
    ) -> SessionMessage:
        self._ensure_connected()
        assert self.pool is not None

        message_id = uuid4()
        now = datetime.now(UTC)
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                session_exists = await conn.fetchval(
                    """
                    SELECT 1
                    FROM sessions
                    WHERE user_id = $1 AND session_id = $2
                    """,
                    user_id,
                    session_id,
                )
                if not session_exists:
                    raise ValueError("Session not found")

                row = await conn.fetchrow(
                    """
                    INSERT INTO session_messages (
                        message_id, session_id, role, content, created_at, updated_at
                    )
                    VALUES ($1, $2, $3, $4, $5, $5)
                    RETURNING message_id, role, content, created_at, updated_at
                    """,
                    message_id,
                    session_id,
                    role,
                    content,
                    now,
                )
                await conn.execute(
                    """
                    UPDATE sessions
                    SET updated_at = $3
                    WHERE user_id = $1 AND session_id = $2
                    """,
                    user_id,
                    session_id,
                    now,
                )

        return self._row_to_message(row)

    async def list_messages(
        self,
        user_id: str,
        session_id: UUID,
        limit: int = 0,
    ) -> list[SessionMessage]:
        self._ensure_connected()
        assert self.pool is not None

        if limit > 0:
            rows = await self.pool.fetch(
                """
                SELECT message_id, role, content, created_at, updated_at
                FROM (
                    SELECT m.message_id, m.role, m.content, m.created_at, m.updated_at
                    FROM session_messages m
                    INNER JOIN sessions s ON s.session_id = m.session_id
                    WHERE s.user_id = $1 AND s.session_id = $2
                    ORDER BY m.created_at DESC
                    LIMIT $3
                ) recent
                ORDER BY created_at ASC
                """,
                user_id,
                session_id,
                limit,
            )
        else:
            rows = await self.pool.fetch(
                """
                SELECT m.message_id, m.role, m.content, m.created_at, m.updated_at
                FROM session_messages m
                INNER JOIN sessions s ON s.session_id = m.session_id
                WHERE s.user_id = $1 AND s.session_id = $2
                ORDER BY m.created_at ASC
                """,
                user_id,
                session_id,
            )
        return [self._row_to_message(row) for row in rows]


postgres_store = PostgresStore()
