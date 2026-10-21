from datetime import UTC, datetime
from typing import Any, Literal
from uuid import UUID, uuid4

import asyncpg
from loguru import logger

from src.models.session import Session, SessionMessage


DEFAULT_SESSION_NAME = "New session"


class PostgresStore:
    """
    PostgreSQL-backed store for chat sessions and session messages.

    Persists the Studio chat history in normalized relational tables and exposes
    session-scoped operations for creating conversations, listing recent
    sessions, renaming sessions, and appending or reading messages.

    Conceptual model
    ----------------
    User -> multiple Sessions -> ordered SessionMessages

    Identity
    --------
    Sessions and messages are identified by generated UUID primary keys:
        sessions.session_id
        session_messages.message_id

    User ownership is enforced by every public read and write operation that
    accepts a user_id. Messages are only accessible through their owning session.

    Stored data
    -----------
    Each session stores:
        session_id
        user_id
        name
        updated_at

    Each message stores:
        message_id
        session_id
        role
        content
        created_at
        updated_at

    Behaviour
    ---------
    - connect() initializes the required schema if it does not already exist
    - create_session() creates a named session for a user
    - add_message() appends a message and refreshes the session updated_at value
    - list_messages() returns messages in chronological order
    - deleting a session cascades to its messages through the database schema

    Consistency guarantees
    ----------------------
    - add_message() validates session ownership before inserting
    - message insertion and session timestamp update run in one transaction
    - list_sessions() and get_latest_session() order by most recently updated
    """

    def __init__(self) -> None:
        self.pool: asyncpg.Pool | None = None

    async def connect(self, config_dict: dict) -> None:
        """
        Connect to Postgres and initialize the sessions schema.

        Parameters
        ----------
        config_dict
            Dictionary containing ``postgres_url``, an asyncpg-compatible
            PostgreSQL connection URL.

            Example::

                {
                    "postgres_url": (
                        "postgresql://user:password@localhost:5432/studio"
                    )
                }

        The method is idempotent for an already connected store.
        """
        if self.pool is not None:
            return

        url = config_dict["postgres_url"]
        self.pool = await asyncpg.create_pool(url)
        await self._init_schema()
        logger.info(f"✓ Connected to Postgres at {url}")

    async def close(self) -> None:
        """Close the connection pool if it is open."""
        if self.pool is None:
            return

        await self.pool.close()
        self.pool = None
        logger.info("✓ Closed Postgres connection")

    def _ensure_connected(self) -> None:
        """Ensure the connection pool has been initialized."""
        if self.pool is None:
            raise RuntimeError(
                f"{self.__class__.__name__} used before connect() was called"
            )

    async def _init_schema(self) -> None:
        """Create the session and message tables required by the store."""
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

            await conn.execute(
                """
                ALTER TABLE sessions
                ADD COLUMN IF NOT EXISTS message_count INT NOT NULL DEFAULT 0
                """
            )
            await conn.execute(
                """
                ALTER TABLE sessions
                ADD COLUMN IF NOT EXISTS title_type TEXT NOT NULL DEFAULT 'static'
                """
            )
            await conn.execute(
                """
                ALTER TABLE sessions
                ADD COLUMN IF NOT EXISTS title_overwritten BOOLEAN NOT NULL DEFAULT FALSE
                """
            )
            await conn.execute(
                """
                ALTER TABLE sessions
                ADD COLUMN IF NOT EXISTS last_title_message_count INT NOT NULL DEFAULT 0
                """
            )

    @staticmethod
    def _row_to_session(row: Any) -> Session:
        return Session(
            session_id=row["session_id"],
            user_id=row["user_id"],
            name=row["name"],
            updated_at=row["updated_at"],
            message_count=row["message_count"],
            title_type=row["title_type"],
            title_overwritten=row["title_overwritten"],
            last_title_message_count=row["last_title_message_count"],
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
        title_type: str = "static",
    ) -> Session:
        """Create and return a new session for a user."""
        self._ensure_connected()
        assert self.pool is not None

        session_id = uuid4()
        now = datetime.now(UTC)
        row = await self.pool.fetchrow(
            """
            INSERT INTO sessions (session_id, user_id, name, updated_at,
                                  message_count, title_type, title_overwritten,
                                  last_title_message_count)
            VALUES ($1, $2, $3, $4, 0, $5, FALSE, 0)
            RETURNING session_id, user_id, name, updated_at,
                      message_count, title_type, title_overwritten,
                      last_title_message_count
            """,
            session_id,
            user_id,
            name,
            now,
            title_type,
        )
        return self._row_to_session(row)

    async def list_sessions(self, user_id: str) -> list[Session]:
        """Return a user's sessions ordered by most recently updated first."""
        self._ensure_connected()
        assert self.pool is not None

        rows = await self.pool.fetch(
            """
            SELECT session_id, user_id, name, updated_at,
                   message_count, title_type, title_overwritten,
                   last_title_message_count
            FROM sessions
            WHERE user_id = $1
            ORDER BY updated_at DESC
            """,
            user_id,
        )
        return [self._row_to_session(row) for row in rows]

    async def get_latest_session(self, user_id: str) -> Session | None:
        """Return the most recently updated session for a user, if one exists."""
        self._ensure_connected()
        assert self.pool is not None

        row = await self.pool.fetchrow(
            """
            SELECT session_id, user_id, name, updated_at,
                   message_count, title_type, title_overwritten,
                   last_title_message_count
            FROM sessions
            WHERE user_id = $1
            ORDER BY updated_at DESC
            LIMIT 1
            """,
            user_id,
        )
        return self._row_to_session(row) if row else None

    async def get_session(self, user_id: str, session_id: UUID) -> Session | None:
        """Return a session by id when it belongs to the given user."""
        self._ensure_connected()
        assert self.pool is not None

        row = await self.pool.fetchrow(
            """
            SELECT session_id, user_id, name, updated_at,
                   message_count, title_type, title_overwritten,
                   last_title_message_count
            FROM sessions
            WHERE user_id = $1 AND session_id = $2
            """,
            user_id,
            session_id,
        )
        return self._row_to_session(row) if row else None

    async def delete_session(self, user_id: str, session_id: UUID) -> bool:
        self._ensure_connected()
        assert self.pool is not None

        result = await self.pool.execute(
            "DELETE FROM sessions WHERE user_id = $1 AND session_id = $2",
            user_id,
            session_id,
        )
        return result != "DELETE 0"

    async def update_session_name(
        self,
        user_id: str,
        session_id: UUID,
        name: str,
        current_name: str | None = DEFAULT_SESSION_NAME,
    ) -> Session | None:
        """
        Update a session name and return the updated session.

        When current_name is provided, the update only succeeds if the existing
        name still matches it. Passing None updates the name unconditionally.
        """
        self._ensure_connected()
        assert self.pool is not None

        if current_name is None:
            row = await self.pool.fetchrow(
                """
                UPDATE sessions
                SET name = $3
                WHERE user_id = $1 AND session_id = $2
                RETURNING session_id, user_id, name, updated_at,
                          message_count, title_type, title_overwritten,
                          last_title_message_count
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
                RETURNING session_id, user_id, name, updated_at,
                          message_count, title_type, title_overwritten,
                          last_title_message_count
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
        """
        Append a message to a user-owned session.

        Raises ValueError when the session does not exist for the given user.
        The message insert and parent session updated_at refresh are committed
        in the same transaction.
        """
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
        """
        Return messages for a user-owned session in chronological order.

        When limit is greater than zero, only the latest limit messages are
        returned, still ordered from oldest to newest.
        """
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

    async def increment_message_count(
        self,
        user_id: str,
        session_id: UUID,
    ) -> None:
        """Increment the message counter for a session."""
        self._ensure_connected()
        assert self.pool is not None

        await self.pool.execute(
            """
            UPDATE sessions
            SET message_count = message_count + 1
            WHERE user_id = $1 AND session_id = $2
            """,
            user_id,
            session_id,
        )

    async def update_session_meta(
        self,
        user_id: str,
        session_id: UUID,
        name: str | None = None,
        title_type: str | None = None,
        title_overwritten: bool | None = None,
        last_title_message_count: int | None = None,
    ) -> Session | None:
        """Update session metadata fields. Only non-None values are applied."""
        self._ensure_connected()
        assert self.pool is not None

        sets: list[str] = []
        params: list[Any] = []
        idx = 3

        if name is not None:
            sets.append(f"name = ${idx}")
            params.append(name)
            idx += 1
        if title_type is not None:
            sets.append(f"title_type = ${idx}")
            params.append(title_type)
            idx += 1
        if title_overwritten is not None:
            sets.append(f"title_overwritten = ${idx}")
            params.append(title_overwritten)
            idx += 1
        if last_title_message_count is not None:
            sets.append(f"last_title_message_count = ${idx}")
            params.append(last_title_message_count)
            idx += 1

        if not sets:
            return await self.get_session(user_id, session_id)

        query = f"""
            UPDATE sessions
            SET {", ".join(sets)}
            WHERE user_id = $1 AND session_id = $2
            RETURNING session_id, user_id, name, updated_at,
                      message_count, title_type, title_overwritten,
                      last_title_message_count
        """
        row = await self.pool.fetchrow(query, user_id, session_id, *params)
        return self._row_to_session(row) if row else None

    async def backfill_message_counts(self) -> int:
        """Set message_count for existing sessions that have count = 0.

        Returns the number of rows updated.
        """
        self._ensure_connected()
        assert self.pool is not None

        result = await self.pool.execute(
            """
            UPDATE sessions s
            SET message_count = (
                SELECT COUNT(*) FROM session_messages m
                WHERE m.session_id = s.session_id
            )
            WHERE s.message_count = 0
            """
        )
        # asyncpg returns e.g. "UPDATE 5"
        count = int(result.split()[-1]) if result else 0
        return count


postgres_store = PostgresStore()
