import os

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from typing import Any
from langfuse import Langfuse, get_client

from backend.endpoints.auth import get_current_user

log_event_router = APIRouter()

Langfuse(
    public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
    secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
    host=os.getenv("LANGFUSE_HOST"),
)


class LogEventPayload(BaseModel):
    name: str
    metadata: dict[str, Any] = Field(default_factory=dict)


@log_event_router.post("/log_event", status_code=204)
async def log_event(payload: LogEventPayload, user=Depends(get_current_user)):
    langfuse = get_client()
    user_id = user.get("sub", "unknown")
    session_id = user.get("sid", user_id)

    trace_id = langfuse.create_trace_id()

    langfuse.create_event(
        trace_context={
            "trace_id": trace_id,
            "user_id": user_id,
            "session_id": session_id,
        },
        name=payload.name,
        metadata=payload.metadata,
    )

    langfuse.flush()


active_trace_ids: dict[str, str] = {}

def start_session(user_id: str, sid: str) -> str:
    langfuse = get_client()
    trace_id = langfuse.create_trace_id()
    active_trace_ids[sid] = trace_id

    with langfuse.start_as_current_observation(
        as_type="span",
        name="session_start",
        trace_context={"trace_id": trace_id, "parent_span_id": "0123456789abcdef"},
    ) as observation:
        observation.update(
            input={"event": "connect", "user_id": user_id, "sid": sid},
            output={"status": "connected", "message": "User connected via Socket.IO"},
        )
        observation.update_trace(
            user_id=user_id,
            session_id=sid,
            metadata={"message": "User connected via Socket.IO"},
        )

    langfuse.flush()
    return trace_id


def end_session(user_id: str | None, sid: str):
    trace_id = active_trace_ids.pop(sid, None)
    if trace_id:
        langfuse = get_client()

        with langfuse.start_as_current_observation(
            as_type="span",
            name="session_end",
            trace_context={"trace_id": trace_id, "parent_span_id": "0123456789abcdef"},
        ) as observation:
            observation.update(
                input={"event": "disconnect", "user_id": user_id, "sid": sid},
                output={
                    "status": "disconnected",
                    "message": "User disconnected / socket closed",
                },
            )
            observation.update_trace(
                user_id=user_id,
                session_id=sid,
                metadata={"message": "User disconnected / socket closed"},
            )

        langfuse.flush()
