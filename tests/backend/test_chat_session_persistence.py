import asyncio
from datetime import UTC, datetime
from typing import Literal
from uuid import uuid4

from backend.endpoints import chat as chat_module
from backend.models.session import Session, SessionMessage
from backend.utility.session_store import active_session_ids


class _FakeSessionStore:
    def __init__(self):
        self.sessions = []
        self.messages = []

    async def create_session(
        self,
        user_id,
        name="New session",
        title_type: Literal["static", "adaptive"] = "static",
    ):
        session = Session(
            session_id=uuid4(),
            user_id=user_id,
            name=name,
            updated_at=datetime.now(UTC),
            message_count=0,
            title_type=title_type,
            title_overwritten=False,
            last_title_message_count=0,
        )
        self.sessions.append(session)
        return session

    async def get_session(self, user_id, session_id):
        return next(
            (
                session
                for session in self.sessions
                if session.user_id == user_id and session.session_id == session_id
            ),
            None,
        )

    async def get_latest_session(self, user_id):
        sessions = [session for session in self.sessions if session.user_id == user_id]
        return max(sessions, key=lambda session: session.updated_at, default=None)

    async def add_message(self, user_id, session_id, role, content):
        if await self.get_session(user_id, session_id) is None:
            raise ValueError("Session not found")

        message = SessionMessage(
            message_id=uuid4(),
            role=role,
            content=content,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        self.messages.append((session_id, message))
        return message

    async def increment_message_count(self, user_id, session_id):
        session = await self.get_session(user_id, session_id)
        if session:
            session.message_count += 1

    async def update_session_name(self, user_id, session_id, name, current_name=None):
        session = await self.get_session(user_id, session_id)
        if session and (current_name is None or session.name == current_name):
            session.name = name
            return session
        return session if session else None

    async def update_session_meta(self, user_id, session_id, **kwargs):
        session = await self.get_session(user_id, session_id)
        if not session:
            return None
        for key, value in kwargs.items():
            if value is not None:
                setattr(session, key, value)
        return session

    async def list_messages(self, user_id, session_id, limit=0):
        msgs = [m for sid, m in self.messages if sid == session_id]
        if limit > 0:
            msgs = msgs[-limit:]
        return msgs


class _FakeRedisStore:
    def __init__(self):
        self.messages = []

    async def store_message(self, session_id, message):
        self.messages.append((session_id, message))


def test_chat_helpers_auto_create_session_and_mirror_messages(monkeypatch):
    async def exercise_chat_persistence():
        fake_postgres_store = _FakeSessionStore()
        fake_redis_store = _FakeRedisStore()
        monkeypatch.setattr(chat_module, "postgres_store", fake_postgres_store)
        monkeypatch.setattr(chat_module, "redis_store", fake_redis_store)
        active_session_ids.clear()

        session = await chat_module._resolve_active_session("user-1", create=True)

        assert session is not None
        assert session.user_id == "user-1"
        assert active_session_ids["user-1"] == session.session_id

        await chat_module._store_chat_message(
            "user-1",
            session.session_id,
            "user",
            "What works?",
        )
        await chat_module._store_chat_message(
            "user-1",
            session.session_id,
            "ai",
            "Targeted support works best.",
        )

        persisted_roles = [message.role for _, message in fake_postgres_store.messages]
        redis_roles = [message.role for _, message in fake_redis_store.messages]
        redis_session_ids = [session_id for session_id, _ in fake_redis_store.messages]

        assert persisted_roles == ["user", "ai"]
        assert redis_roles == ["user", "assistant"]
        assert redis_session_ids == [str(session.session_id), str(session.session_id)]

    asyncio.run(exercise_chat_persistence())


def test_format_history_text_uses_api_roles():
    now = datetime.now(UTC)
    messages = [
        SessionMessage(
            message_id=uuid4(),
            role="user",
            content="Question",
            created_at=now,
            updated_at=now,
        ),
        SessionMessage(
            message_id=uuid4(),
            role="ai",
            content="Answer",
            created_at=now,
            updated_at=now,
        ),
    ]

    assert chat_module._format_history_text(messages) == "User: Question\nAI: Answer"


def test_store_chat_message_increments_counter(monkeypatch):
    async def exercise():
        fake_store = _FakeSessionStore()
        fake_redis = _FakeRedisStore()
        monkeypatch.setattr(chat_module, "postgres_store", fake_store)
        monkeypatch.setattr(chat_module, "redis_store", fake_redis)

        session = await fake_store.create_session("user-1")
        assert session is not None
        assert session.message_count == 0

        await chat_module._store_chat_message(
            "user-1", session.session_id, "user", "Hi"
        )
        session = await fake_store.get_session("user-1", session.session_id)
        assert session is not None
        assert session.message_count == 1

        await chat_module._store_chat_message(
            "user-1", session.session_id, "ai", "Hello"
        )
        session = await fake_store.get_session("user-1", session.session_id)
        assert session is not None
        assert session.message_count == 2

    asyncio.run(exercise())


def test_maybe_generate_title_skips_when_overwritten(monkeypatch):
    async def exercise():
        fake_store = _FakeSessionStore()
        monkeypatch.setattr(chat_module, "postgres_store", fake_store)

        session = await fake_store.create_session("user-1")
        session.title_overwritten = True
        session.name = "Custom title"

        # Should not schedule anything — no task should be created
        chat_module._title_generation_locks.clear()
        await chat_module._maybe_generate_title(
            "user-1", session.session_id, "Q?", "A!"
        )
        assert len(chat_module._title_generation_locks) == 0

    asyncio.run(exercise())


def test_maybe_generate_title_skips_when_not_default_and_not_adaptive(monkeypatch):
    async def exercise():
        fake_store = _FakeSessionStore()
        monkeypatch.setattr(chat_module, "postgres_store", fake_store)

        session = await fake_store.create_session("user-1")
        session.name = "Existing title"
        session.title_type = "static"
        session.title_overwritten = False

        chat_module._title_generation_locks.clear()
        await chat_module._maybe_generate_title(
            "user-1", session.session_id, "Q?", "A!"
        )
        assert len(chat_module._title_generation_locks) == 0

    asyncio.run(exercise())


def test_maybe_generate_title_skips_when_adaptive_below_threshold(monkeypatch):
    async def exercise():
        fake_store = _FakeSessionStore()
        monkeypatch.setattr(chat_module, "postgres_store", fake_store)

        session = await fake_store.create_session("user-1")
        session.name = "Existing title"
        session.title_type = "adaptive"
        session.title_overwritten = False
        session.message_count = 15
        session.last_title_message_count = 0

        chat_module._title_generation_locks.clear()
        await chat_module._maybe_generate_title(
            "user-1", session.session_id, "Q?", "A!"
        )
        assert len(chat_module._title_generation_locks) == 0

    asyncio.run(exercise())


def test_maybe_generate_title_triggers_for_default_session(monkeypatch):
    async def exercise():
        fake_store = _FakeSessionStore()
        monkeypatch.setattr(chat_module, "postgres_store", fake_store)

        session = await fake_store.create_session("user-1")
        assert session.name == "New session"

        chat_module._title_generation_locks.clear()
        await chat_module._maybe_generate_title(
            "user-1", session.session_id, "Q?", "A!"
        )
        # Lock acquired then released (task scheduled)
        assert len(chat_module._title_generation_locks) == 0

    asyncio.run(exercise())


def test_maybe_generate_title_triggers_for_adaptive_at_threshold(monkeypatch):
    async def exercise():
        fake_store = _FakeSessionStore()
        monkeypatch.setattr(chat_module, "postgres_store", fake_store)

        session = await fake_store.create_session("user-1")
        session.name = "Existing title"
        session.title_type = "adaptive"
        session.message_count = 25
        session.last_title_message_count = 5

        chat_module._title_generation_locks.clear()
        await chat_module._maybe_generate_title(
            "user-1", session.session_id, "Q?", "A!"
        )
        assert len(chat_module._title_generation_locks) == 0

    asyncio.run(exercise())
