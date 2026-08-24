import asyncio
import time
from datetime import UTC, datetime
from typing import Literal
from uuid import uuid4

from src.endpoints import chat as chat_module
from src.models.session import Session, SessionMessage, TitleCandidate
from src.utility.session_store import active_session_ids


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


def test_adaptive_approval_mode_emits_candidate_without_applying(monkeypatch):
    async def exercise():
        fake_store = _FakeSessionStore()
        monkeypatch.setattr(chat_module, "postgres_store", fake_store)
        monkeypatch.setattr(
            chat_module, "_generate_adaptive_title", _async_title("Suggested title")
        )
        emissions: list[tuple[str, str, dict[str, object]]] = []
        monkeypatch.setattr(
            chat_module, "emit_to_user", _async_emit_collector(emissions)
        )

        session = await fake_store.create_session("user-1")
        session.title_type = "adaptive"
        session.name = "Existing title"
        session.message_count = 25
        session.last_title_message_count = 5

        chat_module.user_title_settings["user-1"] = False
        chat_module._pending_title_candidates.clear()
        try:
            await chat_module._update_session_title_adaptive(
                "user-1", session.session_id
            )
            updated = await fake_store.get_session("user-1", session.session_id)
            assert updated is not None
            assert updated.name == "Existing title"
            assert updated.last_title_message_count == 25

            candidate_emits = [
                e for e in emissions if e[1] == "session_title_candidate"
            ]
            assert len(candidate_emits) == 1
            payload = candidate_emits[0][2]
            assert payload["session_id"] == str(session.session_id)
            assert payload["name"] == "Suggested title"
            assert payload["candidate_id"] in chat_module._pending_title_candidates
        finally:
            _ = chat_module.user_title_settings.pop("user-1", None)
            chat_module._pending_title_candidates.clear()

    asyncio.run(exercise())


def test_adaptive_autoapply_mode_applies_and_emits(monkeypatch):
    async def exercise():
        fake_store = _FakeSessionStore()
        monkeypatch.setattr(chat_module, "postgres_store", fake_store)
        monkeypatch.setattr(
            chat_module, "_generate_adaptive_title", _async_title("Auto title")
        )
        emissions: list[tuple[str, str, dict[str, object]]] = []
        monkeypatch.setattr(
            chat_module, "emit_to_user", _async_emit_collector(emissions)
        )

        session = await fake_store.create_session("user-1")
        session.title_type = "adaptive"
        session.name = "Existing title"
        session.message_count = 25
        session.last_title_message_count = 5

        chat_module.user_title_settings["user-1"] = True
        chat_module._pending_title_candidates.clear()
        try:
            await chat_module._update_session_title_adaptive(
                "user-1", session.session_id
            )
            updated = await fake_store.get_session("user-1", session.session_id)
            assert updated is not None
            assert updated.name == "Auto title"
            assert updated.last_title_message_count == 25
            assert len(chat_module._pending_title_candidates) == 0

            updated_emits = [
                e for e in emissions if e[1] == "session_title_updated"
            ]
            assert len(updated_emits) == 1
            assert updated_emits[0][2]["name"] == "Auto title"
            assert updated_emits[0][2]["previous_name"] == "Existing title"
        finally:
            _ = chat_module.user_title_settings.pop("user-1", None)
            chat_module._pending_title_candidates.clear()

    asyncio.run(exercise())


def test_title_revert_restores_previous_name(monkeypatch):
    async def exercise():
        fake_store = _FakeSessionStore()
        monkeypatch.setattr(chat_module, "postgres_store", fake_store)
        emissions: list[tuple[str, str, dict[str, object]]] = []
        monkeypatch.setattr(
            chat_module, "emit_to_user", _async_emit_collector(emissions)
        )
        monkeypatch.setattr(chat_module, "sid_connections", {"sid-1": "user-1"})

        session = await fake_store.create_session("user-1")
        session.name = "Auto title"
        session.message_count = 25
        session.last_title_message_count = 25
        session.title_overwritten = False
        try:
            await chat_module.session_title_revert(
                "sid-1",
                {"session_id": str(session.session_id), "name": "Existing title"},
            )
            updated = await fake_store.get_session("user-1", session.session_id)
            assert updated is not None
            assert updated.name == "Existing title"
            assert updated.title_overwritten is False
            assert updated.last_title_message_count == 25

            updated_emits = [
                e for e in emissions if e[1] == "session_title_updated"
            ]
            assert len(updated_emits) == 1
            assert updated_emits[0][2]["name"] == "Existing title"
            assert "previous_name" not in updated_emits[0][2]
        finally:
            chat_module._pending_title_candidates.clear()

    asyncio.run(exercise())


def test_title_candidate_accept_applies_and_emits(monkeypatch):
    async def exercise():
        fake_store = _FakeSessionStore()
        monkeypatch.setattr(chat_module, "postgres_store", fake_store)
        emissions: list[tuple[str, str, dict[str, object]]] = []
        monkeypatch.setattr(
            chat_module, "emit_to_user", _async_emit_collector(emissions)
        )
        monkeypatch.setattr(chat_module, "sid_connections", {"sid-1": "user-1"})

        session = await fake_store.create_session("user-1")
        session.name = "Existing title"

        candidate_id = str(uuid4())
        chat_module._pending_title_candidates[candidate_id] = TitleCandidate(
            user_id="user-1",
            session_id=session.session_id,
            name="Accepted title",
            expires_at=time.time() + 60,
        )
        try:
            await chat_module.session_title_accept(
                "sid-1", {"candidate_id": candidate_id}
            )
            updated = await fake_store.get_session("user-1", session.session_id)
            assert updated is not None
            assert updated.name == "Accepted title"
            assert candidate_id not in chat_module._pending_title_candidates

            updated_emits = [
                e for e in emissions if e[1] == "session_title_updated"
            ]
            assert len(updated_emits) == 1
            assert updated_emits[0][2]["name"] == "Accepted title"
        finally:
            chat_module._pending_title_candidates.clear()

    asyncio.run(exercise())


def test_title_candidate_reject_discards_without_change(monkeypatch):
    async def exercise():
        fake_store = _FakeSessionStore()
        monkeypatch.setattr(chat_module, "postgres_store", fake_store)
        emissions: list[tuple[str, str, dict[str, object]]] = []
        monkeypatch.setattr(
            chat_module, "emit_to_user", _async_emit_collector(emissions)
        )
        monkeypatch.setattr(chat_module, "sid_connections", {"sid-1": "user-1"})

        session = await fake_store.create_session("user-1")
        session.name = "Existing title"

        candidate_id = str(uuid4())
        chat_module._pending_title_candidates[candidate_id] = TitleCandidate(
            user_id="user-1",
            session_id=session.session_id,
            name="Rejected title",
            expires_at=time.time() + 60,
        )
        try:
            await chat_module.session_title_reject(
                "sid-1", {"candidate_id": candidate_id}
            )
            updated = await fake_store.get_session("user-1", session.session_id)
            assert updated is not None
            assert updated.name == "Existing title"
            assert candidate_id not in chat_module._pending_title_candidates
            assert emissions == []
        finally:
            chat_module._pending_title_candidates.clear()

    asyncio.run(exercise())


def test_title_candidate_expired_accept_is_noop(monkeypatch):
    async def exercise():
        fake_store = _FakeSessionStore()
        monkeypatch.setattr(chat_module, "postgres_store", fake_store)
        emissions: list[tuple[str, str, dict[str, object]]] = []
        monkeypatch.setattr(
            chat_module, "emit_to_user", _async_emit_collector(emissions)
        )
        monkeypatch.setattr(chat_module, "sid_connections", {"sid-1": "user-1"})

        session = await fake_store.create_session("user-1")
        session.name = "Existing title"

        candidate_id = str(uuid4())
        chat_module._pending_title_candidates[candidate_id] = TitleCandidate(
            user_id="user-1",
            session_id=session.session_id,
            name="Stale title",
            expires_at=time.time() - 5,
        )
        try:
            await chat_module.session_title_accept(
                "sid-1", {"candidate_id": candidate_id}
            )
            updated = await fake_store.get_session("user-1", session.session_id)
            assert updated is not None
            assert updated.name == "Existing title"
            assert candidate_id not in chat_module._pending_title_candidates
            assert emissions == []
        finally:
            chat_module._pending_title_candidates.clear()

    asyncio.run(exercise())


def _async_title(title: str):
    async def stub(*args: object, **kwargs: object) -> str:
        return title

    return stub


def _async_emit_collector(emissions: list[tuple[str, str, dict[str, object]]]):
    async def stub(user_id: str, event: str, payload: dict[str, object]):
        emissions.append((user_id, event, payload))

    return stub


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
