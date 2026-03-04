import json
import time
from collections import defaultdict
from typing import List, TypedDict, DefaultDict

import httpx
import socketio
from fastapi import APIRouter

from backend.config import LLM_WORKER_URL, LLM_WORKER_PORT, BASE_URL
from backend.endpoints.graph import (
    user_graph_contexts,
    _default_user_graph_context
)
from backend.endpoints.graph import fetch_subnode_stream
from src.backend.utility.chat_util import (
    register_socketio,
    bind_user,
    unbind_sid,
    push_chat_message_stream,
    sid_connections,
)

# =====================================================
# SOCKET.IO SERVER
# =====================================================

# Build list of allowed CORS origins for Socket.IO
cors_origins = [BASE_URL]

sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins=cors_origins,
    cors_credentials=True,
)

register_socketio(sio)

socket_app = socketio.ASGIApp(sio)
chat_router = APIRouter()


# =====================================================
# Session Models
# =====================================================

class Session(TypedDict):
    history: List[dict]
    last_seen: float
    last_topic: str | None


user_sessions: DefaultDict[str, Session] = defaultdict(
    lambda: {"history": [], "last_seen": time.time(), "last_topic": None}
)


# =====================================================
# SOCKET.IO EVENT HANDLERS
# =====================================================

@sio.event
async def connect(sid, environ, auth):
    """
    Called when a client initiates a Socket.IO connection.
    Loads user from ASGI session (already decoded by SessionMiddleware).
    """
    scope = environ.get("asgi.scope") or {}
    session = scope.get("session") or {}
    user = session.get("user")

    if not user:
        print("❌ Rejecting socket: no user in session")
        raise ConnectionRefusedError("unauthorized")

    user_id = user["sub"]
    bind_user(user_id, sid)
    user_graph_contexts[user_id] = _default_user_graph_context()
    
    print(f"✓ Socket connected: {sid} user={user_id}")


@sio.event
async def disconnect(sid):
    user_id = unbind_sid(sid)
    print(f"⚠ Socket disconnected sid={sid} user={user_id}")


# =====================================================
# MAIN MESSAGE HANDLER
# =====================================================
@sio.event
async def send_message(sid, data):
    user_id = sid_connections.get(sid)
    if not user_id:
        return

    user_msg = (data.get("message") or "").strip()
    if not user_msg:
        return

    session = user_sessions.setdefault(user_id, {"history": []})
    ctx = user_graph_contexts[user_id]

    selected_subnode = ctx.get("selected_subnode", "root")
    dialogue_state_asked = bool(ctx.get("dialogue_state_asked", False))
    prefetched = (ctx.get("prefetched") or {}).get(selected_subnode)

    if dialogue_state_asked:
        try:
            if user_msg.lower() == "yes":
                # Use prefetched if available
                if prefetched:
                    await push_chat_message_stream(
                        user_id,
                        "on_chat_model_stream",
                        prefetched,
                        selected_subnode,
                    )
                    await push_chat_message_stream(
                        user_id,
                        "done",
                        prefetched,
                        selected_subnode,
                    )
                    return

                question = ctx.get("latest_question") or ctx.get("previous_question")
            else:
                ctx["latest_question"] = user_msg
                ctx["prefetched"] = {}
                question = ctx["latest_question"]

            await fetch_subnode_stream(user_id, question, selected_subnode)
            await push_chat_message_stream(
                    user_id,
                    "done",
                    ctx.get("prefetched", {}).get(selected_subnode),
                    selected_subnode,
                )
            return

        finally:
            ctx["dialogue_state_asked"] = False


    # --------------------------------------------------
    # NORMAL ROOT WORKFLOW (user asked a new question in chat)
    # --------------------------------------------------
    session["history"].append({"role": "user", "message": user_msg})

    ctx["previous_question"] = ctx.get("latest_question")
    ctx["latest_question"] = user_msg
    ctx["selected_subnode"] = "root"
    ctx["dialogue_state_asked"] = False

    synthetic_prompt = (
        "SYSTEM META-INSTRUCTION:\n"
        "Use the `get_literature_supported_knowledge` MCP tool to identify sources relevant to the question.\n\n"
        f"full_question:\n\"{user_msg}\"\n\n"
        "keywords_related_to_question=\"Best practices || Target groups || Strategic overview\"\n"
        "Provide an evidence-informed explanation when possible.\n"
    )

    worker_url = f"{LLM_WORKER_URL}:{LLM_WORKER_PORT}"
    full_response = ""

    async with httpx.AsyncClient(timeout=None) as client:
        async with client.stream(
            "POST",
            f"{worker_url}/ask_stream",
            json={
                "chat_id": "default",
                "message": synthetic_prompt,
                "user_id": user_id,
            },
        ) as resp:

            if resp.status_code != 200:
                err = "❌ Error: worker unavailable"
                await push_chat_message_stream(user_id, "on_chat_model_stream", err, "root")
                await push_chat_message_stream(user_id, "done", err, "root")
                return

            async for line in resp.aiter_lines():
                if not line.startswith("data:"):
                    continue

                raw = line.removeprefix("data:").strip()
                if raw == "[DONE]":
                    break

                try:
                    payload = json.loads(raw)
                except json.JSONDecodeError:
                    continue

                event_type = payload.get("type")
                event_data = payload.get("data") or ""

                # Forward events (tool/status/etc.) to frontend event channel
                # NOTE: your push_chat_message_stream will emit these via "event"
                if event_type != "on_chat_model_stream":
                    await push_chat_message_stream(user_id, event_type, event_data, "root")
                    continue

                # Stream tokens to chat UI
                if event_data:
                    await push_chat_message_stream(
                        user_id,
                        "on_chat_model_stream",
                        event_data,
                        "root",
                    )
                    full_response += event_data

    # --------------------------------------------------
    # FINALIZE ROOT RESPONSE
    # --------------------------------------------------
    session["history"].append({"role": "assistant", "message": full_response})
    ctx.setdefault("prefetched", {})["root"] = full_response

    await push_chat_message_stream(user_id, "done", full_response, "root")
