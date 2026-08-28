from typing import Any
from uuid import UUID


ACTIVE_SESSION_KEY = "active_session_id"

active_session_ids: dict[str, UUID] = {}


def set_active_session_id(user_id: str, session_id: UUID) -> None:
    active_session_ids[user_id] = session_id


def get_active_session_id(user_id: str) -> UUID | None:
    return active_session_ids.get(user_id)


def parse_session_id(value: Any) -> UUID | None:
    if value is None:
        return None
    if isinstance(value, UUID):
        return value
    try:
        return UUID(str(value))
    except (TypeError, ValueError):
        return None
