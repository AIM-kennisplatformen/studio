from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from typing import Any
from langfuse import get_client

from backend.endpoints.auth import get_current_user
from backend.utility.chat_util import user_connections
from backend.utility.log_util import active_trace_ids

log_event_router = APIRouter()


class LogEventPayload(BaseModel):
    name: str
    metadata: dict[str, Any] = Field(default_factory=dict)


@log_event_router.post("/log_event", status_code=204)
async def log_event(payload: LogEventPayload, user=Depends(get_current_user)):
    langfuse = get_client()
    user_id = user["sub"]
    session_id = user_connections[user_id]

    trace_id = active_trace_ids.get(session_id, None)

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
