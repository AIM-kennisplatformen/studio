import asyncio
from datetime import UTC, datetime
from typing import Literal
from uuid import uuid4

import pytest
from fastapi import HTTPException

from backend.endpoints import sessions as sessions_module
from backend.models.session import Session, SessionMessage
from backend.utility.session_store import ACTIVE_SESSION_KEY, active_session_ids


class _FakeSessionStore:
    def __init__(self):
        self.session = Session(
            session_id=uuid4(),
            user_id="user-1",
            name="Energy Poverty Actions",
            updated_at=datetime.now(UTC),
            message_count=2,
            title_type="static",
            title_overwritten=False,
            last_title_message_count=0,
        )
        self.foreign_session = Session(
            session_id=uuid4(),
            user_id="user-2",
            name="Foreign",
            updated_at=datetime.now(UTC),
            message_count=0,
            title_type="static",
            title_overwritten=False,
            last_title_message_count=0,
        )
        self.messages = [
            SessionMessage(
                message_id=uuid4(),
                role="user",
                content="What works?",
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            ),
            SessionMessage(
                message_id=uuid4(),
                role="ai",
                content="Targeted support works best.",
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            ),
        ]

    async def create_session(
        self,
        user_id,
        name="New session",
        title_type: Literal["static", "adaptive"] = "static",
    ):
        self.created_session = Session(
            session_id=uuid4(),
            user_id=user_id,
            name=name,
            updated_at=datetime.now(UTC),
            message_count=0,
            title_type=title_type,
            title_overwritten=False,
            last_title_message_count=0,
        )
        return self.created_session

    async def list_sessions(self, user_id):
        return [self.session] if user_id == self.session.user_id else []

    async def get_session(self, user_id, session_id):
        if user_id == self.session.user_id and session_id == self.session.session_id:
            return self.session
        return None

    async def list_messages(self, user_id, session_id):
        if user_id == self.session.user_id and session_id == self.session.session_id:
            return self.messages
        return []

    async def update_session_meta(self, user_id, session_id, **kwargs):
        if user_id != self.session.user_id or session_id != self.session.session_id:
            return None
        for key, value in kwargs.items():
            if value is not None:
                setattr(self.session, key, value)
        return self.session


class _FakeRequest:
    def __init__(self):
        self.session = {}


def _install_fake_store(monkeypatch, fake_store):
    monkeypatch.setattr(sessions_module, "postgres_store", fake_store)


def test_list_sessions_returns_only_current_user_sessions(monkeypatch):
    async def exercise_endpoint():
        fake_store = _FakeSessionStore()
        _install_fake_store(monkeypatch, fake_store)

        response = await sessions_module.list_sessions(user={"sub": "user-1"})

        assert response == [fake_store.session]

    asyncio.run(exercise_endpoint())


def test_create_session_updates_http_and_socket_visible_state(monkeypatch):
    async def exercise_endpoint():
        fake_store = _FakeSessionStore()
        request = _FakeRequest()
        _install_fake_store(monkeypatch, fake_store)
        active_session_ids.clear()

        response = await sessions_module.create_session(
            request,
            user={"sub": "user-1"},
        )

        assert response.session_id == fake_store.created_session.session_id
        assert response.user_id == "user-1"
        assert active_session_ids["user-1"] == response.session_id
        assert request.session[ACTIVE_SESSION_KEY] == str(response.session_id)

    asyncio.run(exercise_endpoint())


def test_get_session_returns_session_and_messages(monkeypatch):
    async def exercise_endpoint():
        fake_store = _FakeSessionStore()
        _install_fake_store(monkeypatch, fake_store)

        response = await sessions_module.get_session(
            fake_store.session.session_id,
            user={"sub": "user-1"},
        )

        assert response.session.session_id == fake_store.session.session_id
        assert [message.role for message in response.messages] == ["user", "ai"]
        assert [message.content for message in response.messages] == [
            "What works?",
            "Targeted support works best.",
        ]

    asyncio.run(exercise_endpoint())


def test_get_session_returns_404_for_foreign_session(monkeypatch):
    async def exercise_endpoint():
        fake_store = _FakeSessionStore()
        _install_fake_store(monkeypatch, fake_store)

        with pytest.raises(HTTPException) as exc:
            await sessions_module.get_session(
                fake_store.foreign_session.session_id,
                user={"sub": "user-1"},
            )

        assert exc.value.status_code == 404

    asyncio.run(exercise_endpoint())


def test_activate_session_updates_http_and_socket_visible_state(monkeypatch):
    async def exercise_endpoint():
        fake_store = _FakeSessionStore()
        request = _FakeRequest()
        _install_fake_store(monkeypatch, fake_store)
        active_session_ids.clear()

        response = await sessions_module.activate_session(
            fake_store.session.session_id,
            request,
            user={"sub": "user-1"},
        )

        assert response.session_id == fake_store.session.session_id
        assert active_session_ids["user-1"] == fake_store.session.session_id
        assert request.session[ACTIVE_SESSION_KEY] == str(fake_store.session.session_id)

    asyncio.run(exercise_endpoint())


def test_update_session_name_sets_overwritten_flag(monkeypatch):
    async def exercise_endpoint():
        fake_store = _FakeSessionStore()
        _install_fake_store(monkeypatch, fake_store)

        from backend.models.session import UpdateSessionRequest

        body = UpdateSessionRequest(name="Custom name")
        response = await sessions_module.update_session(
            fake_store.session.session_id,
            body,
            user={"sub": "user-1"},
        )

        assert response is not None
        assert response.name == "Custom name"
        assert response.title_overwritten is True

    asyncio.run(exercise_endpoint())


def test_update_session_title_type(monkeypatch):
    async def exercise_endpoint():
        fake_store = _FakeSessionStore()
        _install_fake_store(monkeypatch, fake_store)

        from backend.models.session import UpdateSessionRequest

        body = UpdateSessionRequest(title_type="adaptive")
        response = await sessions_module.update_session(
            fake_store.session.session_id,
            body,
            user={"sub": "user-1"},
        )

        assert response is not None
        assert response.title_type == "adaptive"
        assert response.title_overwritten is False  # not changed

    asyncio.run(exercise_endpoint())


def test_update_session_returns_404_for_foreign_session(monkeypatch):
    async def exercise_endpoint():
        fake_store = _FakeSessionStore()
        _install_fake_store(monkeypatch, fake_store)

        from backend.models.session import UpdateSessionRequest

        body = UpdateSessionRequest(name="Hack")
        with pytest.raises(HTTPException) as exc:
            await sessions_module.update_session(
                fake_store.foreign_session.session_id,
                body,
                user={"sub": "user-1"},
            )

        assert exc.value.status_code == 404

    asyncio.run(exercise_endpoint())
