import asyncio
import json
import time
from collections import defaultdict
from typing import List, TypedDict, DefaultDict

import httpx
import socketio
from fastapi import APIRouter

from backend.config import LLM_WORKER_URL, BASE_URL
from backend.endpoints.graph import (
    user_graph_contexts,
    SUBNODES,
    prefetch_subnode,
)

from src.backend.utility.chat_util import (
    register_socketio,
    bind_user,
    unbind_sid,
    sid_connections,
)

# =====================================================
# SOCKET.IO SERVER
# =====================================================

sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins=[BASE_URL],
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
    """
    Frontend emits:
        socket.emit("send_message", { message: "..." })

    This function:
    - resolves user_id
    - updates session & graph context
    - streams LLM response token-by-token
    - kicks off subnode prefetch tasks
    """

    # --- Resolve user ---
    user_id = sid_connections.get(sid)
    if not user_id:
        print(f"❌ No user mapped to sid {sid}")
        return

    user_msg = data.get("message", "")
    print(f"[{user_id}] USER:", user_msg)

    # --- Update session ---
    session = user_sessions[user_id]
    session["history"].append({"role": "user", "message": user_msg})
    session["last_seen"] = time.time()

    # --- Update graph context ---
    ctx = user_graph_contexts[user_id]
    ctx["latest_question"] = user_msg
    ctx["selected_subnode"] = "root"

    # --- Build LLM prompt ---
    synthetic_prompt = (
        "SYSTEM META-INSTRUCTION:\n"
        "Use the `paper_search` MCP tool to identify sources relevant to the question.\n\n"
        f"full_question:\n\"{user_msg}\"\n\n"
        "keywords_related_to_question=\"Best practices || Target groups || Strategic overview\" "
        "Provide an evidence-informed explanation when possible.\n"
    )

    # =====================================================
    # STREAM ROOT RESPONSE FROM LLM WORKER
    # =====================================================

    async with httpx.AsyncClient(timeout=httpx.Timeout(300)) as client:
        resp = await client.post(
            f"{LLM_WORKER_URL}/ask_stream",
            json={
                "chat_id": "default",
                "message": synthetic_prompt,
                "user_id": user_id,
            },
        )

    if resp.status_code != 200:
        await sio.emit(
            "message",
            {"role": "chatbot", "content": "Error: worker unavailable"},
            to=sid,
        )
        return

    full_response = ""

    async for line in resp.aiter_lines():
        if not line.strip():
            continue

        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue

        # --- Streaming tokens ---
        if "token" in payload:
            token = payload["token"]
            full_response += token
            await sio.emit("message", {"role": "chatbot", "content": token}, to=sid)
            continue

        # --- Optional metadata ---
        if "topic" in payload:
            session["last_topic"] = payload["topic"]

        # --- Completion ---
        if payload.get("done"):
            await sio.emit("done", {"full_response": full_response}, to=sid)
            break

    # --- Store full root answer ---
    ctx["prefetched"]["root"] = full_response
    session["history"].append(
        {"role": "assistant", "message": full_response}
    )

    # =====================================================
    # KICK OFF SUBNODE PREFETCH (async background tasks)
    # =====================================================
    for subnode in SUBNODES:
        if subnode not in ctx["pending"] and subnode not in ctx["prefetched"]:
            ctx["pending"][subnode] = asyncio.create_task(
                prefetch_subnode(
                    user_id=user_id,
                    question=user_msg,
                    subnode=subnode,
                )
            )
