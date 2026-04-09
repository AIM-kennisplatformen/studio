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
