import asyncio
from uuid import uuid4

import pytest

from backend.stores.postgres import PostgresStore
from backend.utility.session_store import parse_session_id


class _Context:
    def __init__(self, value):
        self.value = value

    async def __aenter__(self):
        return self.value

    async def __aexit__(self, exc_type, exc, tb):
        return False


class _FakeConnection:
    def __init__(self, pool):
        self.pool = pool

    def transaction(self):
        return _Context(self)

    async def fetchval(self, query, *args):
        user_id, session_id = args
        session = self.pool.sessions.get(session_id)
        return 1 if session and session["user_id"] == user_id else None

    async def fetchrow(self, query, *args):
        normalized = " ".join(query.lower().split())
        if normalized.startswith("insert into session_messages"):
            message_id, session_id, role, content, created_at = args
            row = {
                "message_id": message_id,
                "session_id": session_id,
                "role": role,
                "content": content,
                "created_at": created_at,
                "updated_at": created_at,
            }
            self.pool.messages.append(row)
            return row
        raise AssertionError(f"Unexpected fetchrow query: {query}")

    async def execute(self, query, *args):
        normalized = " ".join(query.lower().split())
        if normalized.startswith("update sessions set updated_at"):
            user_id, session_id, updated_at = args
            session = self.pool.sessions.get(session_id)
            if session and session["user_id"] == user_id:
                session["updated_at"] = updated_at
            return "UPDATE 1"
        return "OK"


class _FakePool:
    def __init__(self):
        self.sessions = {}
        self.messages = []

    def acquire(self):
        return _Context(_FakeConnection(self))

    async def fetchrow(self, query, *args):
        normalized = " ".join(query.lower().split())
        if normalized.startswith("insert into sessions"):
            session_id, user_id, name, updated_at = args
            row = {
                "session_id": session_id,
                "user_id": user_id,
                "name": name,
                "updated_at": updated_at,
            }
            self.sessions[session_id] = row
            return row

        if normalized.startswith("select session_id") and "limit 1" in normalized:
            user_id = args[0]
            sessions = [
                row for row in self.sessions.values() if row["user_id"] == user_id
            ]
            return max(sessions, key=lambda row: row["updated_at"], default=None)

        if normalized.startswith("select session_id") and "where user_id = $1 and session_id = $2" in normalized:
            user_id, session_id = args
            session = self.sessions.get(session_id)
            if session and session["user_id"] == user_id:
                return session
            return None

        if normalized.startswith("update sessions set name = $3"):
            user_id, session_id, name = args
            session = self.sessions.get(session_id)
            if not session or session["user_id"] != user_id:
                return None
            session["name"] = name
            return session

        if normalized.startswith("update sessions set name = $4"):
            user_id, session_id, current_name, name = args
            session = self.sessions.get(session_id)
            if (
                not session
                or session["user_id"] != user_id
                or session["name"] != current_name
            ):
                return None
            session["name"] = name
            return session

        raise AssertionError(f"Unexpected fetchrow query: {query}")

    async def fetch(self, query, *args):
        normalized = " ".join(query.lower().split())
        if normalized.startswith("select session_id"):
            user_id = args[0]
            sessions = [
                row for row in self.sessions.values() if row["user_id"] == user_id
            ]
            return sorted(sessions, key=lambda row: row["updated_at"], reverse=True)

        if "from session_messages" in normalized:
            user_id, session_id = args[:2]
            session = self.sessions.get(session_id)
            if not session or session["user_id"] != user_id:
                return []

            messages = [
                row for row in self.messages if row["session_id"] == session_id
            ]
            if len(args) == 3:
                messages = sorted(
                    messages,
                    key=lambda row: row["created_at"],
                    reverse=True,
                )[: args[2]]
            return sorted(messages, key=lambda row: row["created_at"])

        raise AssertionError(f"Unexpected fetch query: {query}")


def test_parse_session_id_accepts_uuid_and_rejects_invalid_values():
    session_id = uuid4()

    assert parse_session_id(session_id) == session_id
    assert parse_session_id(str(session_id)) == session_id
    assert parse_session_id("not-a-uuid") is None
    assert parse_session_id(None) is None


def test_postgres_store_public_methods_with_fake_pool():
    async def exercise_store():
        store = PostgresStore()
        store.pool = _FakePool()

        session = await store.create_session("user-1", "New session")
        other_session = await store.create_session("user-2", "Other")
        old_updated_at = session.updated_at

        user_message = await store.add_message(
            "user-1",
            session.session_id,
            "user",
            "How can we reduce energy poverty?",
        )
        ai_message = await store.add_message(
            "user-1",
            session.session_id,
            "ai",
            "Start with targeted household support.",
        )

        messages = await store.list_messages("user-1", session.session_id)
        assert [message.message_id for message in messages] == [
            user_message.message_id,
            ai_message.message_id,
        ]
        assert [message.role for message in messages] == ["user", "ai"]

        limited_messages = await store.list_messages("user-1", session.session_id, 1)
        assert [message.message_id for message in limited_messages] == [
            ai_message.message_id
        ]
        assert await store.list_messages("user-2", session.session_id) == []

        with pytest.raises(ValueError):
            await store.add_message("user-2", session.session_id, "user", "Nope")

        sessions = await store.list_sessions("user-1")
        assert [item.session_id for item in sessions] == [session.session_id]
        assert other_session.user_id == "user-2"

        updated_session = await store.get_session("user-1", session.session_id)
        assert updated_session is not None
        assert updated_session.updated_at >= old_updated_at

        renamed = await store.update_session_name(
            "user-1",
            session.session_id,
            "Energy Poverty Actions",
        )
        assert renamed is not None
        assert renamed.name == "Energy Poverty Actions"

        skipped = await store.update_session_name(
            "user-1",
            session.session_id,
            "Should Not Replace",
            current_name="New session",
        )
        assert skipped is None

        latest = await store.get_latest_session("user-1")
        assert latest is not None
        assert latest.session_id == session.session_id

    asyncio.run(exercise_store())
