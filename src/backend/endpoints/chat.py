import asyncio
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
    user_id = sid_connections.get(sid)
    if not user_id:
        return

    user_msg = data.get("message", "")
    session = user_sessions[user_id]
    ctx = user_graph_contexts[user_id]

    session["history"].append({"role": "user", "message": user_msg})
    ctx["latest_question"] = user_msg
    ctx["selected_subnode"] = "root"

    synthetic_prompt = (
        "SYSTEM META-INSTRUCTION:\n"
        "Use the `paper_search` MCP tool to identify sources relevant to the question.\n\n"
        f"full_question:\n\"{user_msg}\"\n\n"
        "keywords_related_to_question=\"Best practices || Target groups || Strategic overview\" "
        "Provide an evidence-informed explanation when possible.\n"
    )

    async with httpx.AsyncClient(timeout=httpx.Timeout(300)) as client:
        worker_url = f"{LLM_WORKER_URL}:{LLM_WORKER_PORT}"

        resp = await client.post(
            f"{worker_url}/ask_stream",
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

    # --------------------------------------------------
    # THINK-TAG STATE (important!)
    # --------------------------------------------------
    inside_think = False
    buffer = ""

    async for line in resp.aiter_lines():
        if not line.startswith("data:"):
            continue

        raw = line.removeprefix("data:").strip()

        if raw == "[DONE]":
            await sio.emit("done", {"full_response": full_response}, to=sid)
            break

        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            continue

        if payload.get("type") != "on_chat_model_stream":
            continue

        token = payload.get("data", "")
        if not token:
            continue

        buffer += token

    buffer += token
    THINK_OPEN = "<think>"
    THINK_CLOSE = "</think>"
    MAX_TAG_LEN = max(len(THINK_OPEN), len(THINK_CLOSE))  # 8

    while True:
        if inside_think:
            end = buffer.find(THINK_CLOSE)
            if end == -1:
                # Keep only enough buffer to detect closing tag
                buffer = buffer[-MAX_TAG_LEN:]
                break
            buffer = buffer[end + len(THINK_CLOSE):]
            inside_think = False
            continue

        else:
            start = buffer.find(THINK_OPEN)
            if start == -1:
                # Only emit text that cannot be part of a future <think>
                emit_len = max(0, len(buffer) - MAX_TAG_LEN)
                if emit_len:
                    output = buffer[:emit_len]
                    buffer = buffer[emit_len:]

                    full_response += output
                    await sio.emit(
                        "message",
                        {"role": "chatbot", "content": output},
                        to=sid,
                    )
                break

            # Emit everything before <think>
            if start > 0:
                output = buffer[:start]
                full_response += output
                await sio.emit(
                    "message",
                    {"role": "chatbot", "content": output},
                    to=sid,
                )

            buffer = buffer[start + len(THINK_OPEN):]
            inside_think = True
            continue

    # --------------------------------------------------
    # Kick off subnode prefetch (background)
    # --------------------------------------------------
    for subnode in SUBNODES:
        if subnode not in ctx["pending"] and subnode not in ctx["prefetched"]:
            ctx["pending"][subnode] = asyncio.create_task(
                prefetch_subnode(
                    user_id=user_id,
                    question=user_msg,
                    subnode=subnode,
                )
            )


    # --------------------------------------------------
    # Store clean response
    # --------------------------------------------------
    ctx["prefetched"]["root"] = full_response
    session["history"].append(
        {"role": "assistant", "message": full_response}
    )
