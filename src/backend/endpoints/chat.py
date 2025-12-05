from backend.endpoints.auth import get_current_user
from backend.endpoints.graph import user_graph_contexts, SUBNODES, prefetch_subnode
from backend.chat_helpers.chat_util import active_websockets
from backend.config import LLM_WORKER_URL

from pydantic import BaseModel
from typing import List, Optional, TypedDict, DefaultDict
from collections import defaultdict
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, Depends
import httpx
import asyncio
import json

chat_router = APIRouter()


# ------------------------------------------------------
# Chat + Sessions
# ------------------------------------------------------
class ChatMessage(BaseModel):
    message: str


class Session(TypedDict):
    history: List[dict]
    last_seen: int
    last_topic: str | None


user_sessions: DefaultDict[str, Session] = defaultdict(
    lambda: {
        "history": [],
        "last_seen": 0,
        "last_topic": None,
    }
)
user_locks: DefaultDict[str, asyncio.Lock] = defaultdict(asyncio.Lock)
user_last_request: DefaultDict[str, float] = defaultdict(lambda: 0.0)



# ------------------------------------------------------
# WebSocket Chat
# ------------------------------------------------------
@chat_router.websocket("/ws/chat")
async def chat_websocket(websocket: WebSocket):
    """
    Protected WebSocket endpoint that:
    - validates the session cookie
    - forwards user messages to the LLM worker
    - streams tokens back to the frontend
    - emits a final { type: "done" } event

    Additionally:
    - Tracks per-user graph context
    - On root context (node 1), triggers background prefetch for all three subnodes
    """
    print("something is trying to connect to websocket")
    print("COOKIES:", websocket.headers.get("cookie"))
    print("SESSION:", websocket.session)

    session = websocket.session
    user = session.get("user")

    if not user:
        await websocket.accept()
        await websocket.send_json({"type": "error", "message": "Authentication required"})
        await websocket.close()
        return

    user_id = user["sub"]
    await websocket.accept()
    active_websockets[user_id] = websocket

    print(f"✓ WebSocket connected: {user_id}")

    try:
        while True:
            # Receive user message
            incoming = await websocket.receive_text()
            parsed = json.loads(incoming)
            user_msg = parsed.get("message", "")

            session_data = user_sessions[user_id]
            ctx = user_graph_contexts[user_id]

            # Track question and (optionally) keywords
            ctx["latest_question"] = user_msg
            ctx["latest_keywords"] = []  # TODO: plug in keyword extractor if needed

            # Add user message to history
            session_data["history"].append({
                "role": "user",
                "message": user_msg
            })

            # If we're in root context (no subnode explicitly selected),
            # trigger background prefetch for all subnodes based on this question.
            if ctx["selected_subnode"] is None:
                for subnode in SUBNODES:
                    if subnode not in ctx["pending"]:
                        ctx["pending"][subnode] = asyncio.create_task(
                            prefetch_subnode(
                                user_id=user_id,
                                question=user_msg,
                                subnode=subnode,
                            )
                        )



            synthetic_prompt = (
                "SYSTEM META-INSTRUCTION:\n"
                "use the `paper_search` MCP tool to identify sources relevant to the question.\n\n"
                "Don't alter question and keywords below, insert them straight into tool\n"
                f"full_question:\n\"{user_msg}\"\n\n"
                f"keywords_related_to_question=\"Best practices || Target groups || Strategic overview\" "
                "Provide an evidence-informed explanation when possible.\n"
            )
            # Send to worker /ask_stream (existing behavior)
            async with httpx.AsyncClient(timeout=httpx.Timeout(300)) as client:
                resp = await client.post(
                    f"{LLM_WORKER_URL}/ask_stream",
                    json={
                        "chat_id": "default",
                        "message": synthetic_prompt,
                        "user_id": user_id,
                    }
                )

            if resp.status_code != 200:
                await websocket.send_json({
                    "type": "message",
                    "role": "chatbot",
                    "content": "Error: worker service unavailable"
                })
                continue

            # Stream response from worker
            full_response_text = ""

            async for chunk in resp.aiter_lines():
                if not chunk.strip():
                    continue

                try:
                    payload = json.loads(chunk)
                except Exception:
                    continue

                # Streamed token
                if "token" in payload:
                    token = payload["token"]
                    full_response_text += token

                    await websocket.send_json({
                        "type": "message",
                        "role": "chatbot",
                        "content": token
                    })
                    continue

                # Topic updates
                if "topic" in payload:
                    session_data["last_topic"] = payload["topic"]

                # End of stream
                if payload.get("done"):
                    await websocket.send_json({
                        "type": "done",
                        "full_response": full_response_text
                    })
                    break

            # Store full assistant message
            if full_response_text:
                ctx["prefetched"]["root"] = full_response_text
                session_data["history"].append({
                    "role": "assistant",
                    "message": full_response_text
                })

    except WebSocketDisconnect:
        print(f"⚠ WebSocket disconnected: {user_id}")
        if active_websockets.get(user_id) is websocket:
            active_websockets[user_id] = None
    except Exception as e:
        print("WS error:", e)
        try:
            await websocket.close()
        except Exception:
            pass
        if active_websockets.get(user_id) is websocket:
            active_websockets[user_id] = None
