import asyncio
from datetime import UTC, datetime
from uuid import uuid4

from backend.endpoints import chat as chat_module
from backend.models.session import Session, SessionMessage
from backend.utility.session_store import active_session_ids


class _FakeSessionStore:
    def __init__(self):
        self.sessions = []
        self.messages = []

    async def create_session(self, user_id):
        session = Session(
            session_id=uuid4(),
            user_id=user_id,
            name="New session",
            updated_at=datetime.now(UTC),
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

        persisted_roles = [
            message.role for _, message in fake_postgres_store.messages
        ]
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
