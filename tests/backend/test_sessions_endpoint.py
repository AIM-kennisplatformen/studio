from datetime import UTC, datetime
from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.middleware.sessions import SessionMiddleware

from backend.endpoints import sessions as sessions_module
from backend.endpoints.auth import get_current_user
from backend.models.session import Session, SessionMessage
from backend.utility.session_store import active_session_ids


class _FakeSessionStore:
    def __init__(self):
        self.session = Session(
            session_id=uuid4(),
            user_id="user-1",
            name="Energy Poverty Actions",
            updated_at=datetime.now(UTC),
        )
        self.foreign_session = Session(
            session_id=uuid4(),
            user_id="user-2",
            name="Foreign",
            updated_at=datetime.now(UTC),
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


def _build_client(monkeypatch, fake_store):
    app = FastAPI()
    app.add_middleware(SessionMiddleware, secret_key="test-secret")
    app.dependency_overrides[get_current_user] = lambda: {"sub": "user-1"}
    app.include_router(sessions_module.sessions_router)
    monkeypatch.setattr(sessions_module, "postgres_store", fake_store)
    return TestClient(app)


def test_list_sessions_returns_only_current_user_sessions(monkeypatch):
    fake_store = _FakeSessionStore()
    client = _build_client(monkeypatch, fake_store)

    response = client.get("/sessions/")

    assert response.status_code == 200
    assert response.json() == [
        {
            "session_id": str(fake_store.session.session_id),
            "user_id": "user-1",
            "name": "Energy Poverty Actions",
            "updated_at": fake_store.session.updated_at.isoformat().replace(
                "+00:00", "Z"
            ),
        }
    ]


def test_get_session_returns_session_and_messages(monkeypatch):
    fake_store = _FakeSessionStore()
    client = _build_client(monkeypatch, fake_store)

    response = client.get(f"/sessions/{fake_store.session.session_id}")

    assert response.status_code == 200
    body = response.json()
    assert body["session"]["session_id"] == str(fake_store.session.session_id)
    assert [message["role"] for message in body["messages"]] == ["user", "ai"]
    assert [message["content"] for message in body["messages"]] == [
        "What works?",
        "Targeted support works best.",
    ]


def test_get_session_returns_404_for_foreign_session(monkeypatch):
    fake_store = _FakeSessionStore()
    client = _build_client(monkeypatch, fake_store)

    response = client.get(f"/sessions/{fake_store.foreign_session.session_id}")

    assert response.status_code == 404


def test_activate_session_updates_http_and_socket_visible_state(monkeypatch):
    fake_store = _FakeSessionStore()
    client = _build_client(monkeypatch, fake_store)
    active_session_ids.clear()

    response = client.post(f"/sessions/{fake_store.session.session_id}")

    assert response.status_code == 200
    assert response.json()["session_id"] == str(fake_store.session.session_id)
    assert active_session_ids["user-1"] == fake_store.session.session_id
    assert "session=" in response.headers["set-cookie"]
