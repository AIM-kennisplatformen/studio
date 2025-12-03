from fastapi import FastAPI, HTTPException, Request, Depends, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, FileResponse
from starlette.middleware.sessions import SessionMiddleware

import json
from pydantic import BaseModel
from typing import List, Optional, TypedDict
import os
from authlib.integrations.starlette_client import OAuth
from collections import defaultdict
import asyncio
import time
from typing import DefaultDict
from .models import ContextResponse
from .data_loader import load_knowledge_graph, KnowledgeGraphData
import httpx
from fastapi import WebSocket, WebSocketDisconnect

WORKER_URL = "http://localhost:7000"

# ------------------------------------------------------
# App Setup
# ------------------------------------------------------
app = FastAPI(
    title="Knowledge Graph API",
    description="API for chat-based knowledge graph generation and node context retrieval",
    version="0.1.0"
)

SESSION_SECRET = os.getenv("SESSION_SECRET", "dev-secret-change-me")
app.add_middleware(SessionMiddleware, secret_key=SESSION_SECRET)


# ------------------------------------------------------
# OAuth / Authentik Setup
# ------------------------------------------------------
BASE_URL = os.getenv("BASE_URL", "http://localhost:10090")
DISCOVERY_URL = os.getenv(
    "OAUTH_DISCOVERY_URL",
    "http://auth.localhost:9000/application/o/kg/.well-known/openid-configuration"
)
CLIENT_ID = os.getenv("OAUTH_CLIENT_ID", "rkuclih8uzm44nTUvwasexioUKFk5aG1zhG8jcJX")
CLIENT_SECRET = os.getenv(
    "OAUTH_CLIENT_SECRET",
    "NEb0sAcMc2kTTdvfJMctLYE35Fp0GqyqFp4oOVrstxsevnVMJutiIhvb6TzwPrkbphAh1EiI74oRRO79xRCoZTh1suFYTV9J0tmRJBIFIF4znDYwNyDp3IzUQlESvaS0"
)

oauth = OAuth()
oauth.register(
    name="authentik",
    server_metadata_url=DISCOVERY_URL,
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    client_kwargs={"scope": "openid email profile"},
)


# ------------------------------------------------------
# Knowledge Graph Data
# ------------------------------------------------------
kg_data: Optional[KnowledgeGraphData] = None


def detect_frontend_dir():
    POSSIBLE_FRONTEND_DIRS = [
        "kg/app",
        "kg/frontend/dist",
        "kg/build",
        "kg",
        "app",
        "frontend/dist",
        "build",
        "dist"
    ]

    # Primary detection: must contain assets/
    for d in POSSIBLE_FRONTEND_DIRS:
        index_path = os.path.join(d, "index.html")
        assets_path = os.path.join(d, "assets")
        if os.path.exists(index_path) and os.path.isdir(assets_path):
            return d

    # Fallback: any folder with index.html
    for d in POSSIBLE_FRONTEND_DIRS:
        if os.path.exists(os.path.join(d, "index.html")):
            return d

    return None


def get_index_html():
    d = detect_frontend_dir()
    if not d:
        raise HTTPException(
            500,
            "Frontend build missing — index.html not found in any expected locations."
        )
    return os.path.join(d, "index.html")


@app.on_event("startup")
async def startup_event():
    global kg_data
    kg_data = load_knowledge_graph()
    print(f"✓ Loaded {len(kg_data.entities)} entities")
    print(f"✓ Loaded {len(kg_data.relations)} relations")
    print(f"✓ Loaded {len(kg_data.questions)} questions")

    # Print detected frontend dir on startup
    print(f"✓ Frontend directory detected: {detect_frontend_dir()}")


# ------------------------------------------------------
# CORS
# ------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:10090"],  # exact domain only
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ------------------------------------------------------
# Auth Helpers
# ------------------------------------------------------
def get_current_user(request: Request):
    user = request.session.get("user")

    if not user:
        raise HTTPException(
            status_code=307,
            headers={"Location": "/auth/login"},
        )

    return user


# ------------------------------------------------------
# OAuth Routes
# ------------------------------------------------------
@app.get("/auth/login")
async def login(request: Request):
    redirect_uri = BASE_URL + "/auth/callback"
    return await oauth.authentik.authorize_redirect(request, redirect_uri)


@app.get("/auth/callback")
async def callback(request: Request):
    token = await oauth.authentik.authorize_access_token(request)
    userinfo = token["userinfo"]
    request.session["user"] = dict(userinfo)
    return RedirectResponse("/app")


@app.get("/auth/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/")


@app.get("/me")
async def me(user=Depends(get_current_user)):
    return {"authenticated": True, "user": user}


# ------------------------------------------------------
# Frontend Auto-Detection + Serving
# ------------------------------------------------------
frontend = APIRouter()


@frontend.get("/app/{path:path}")
async def serve_frontend(path: str, user=Depends(get_current_user)):
    d = detect_frontend_dir()
    if not d:
        raise HTTPException(500, "Frontend build not found — no index.html available.")

    # /app/ or /app → index.html
    if path in ["", "/"]:
        return FileResponse(get_index_html())

    requested = os.path.join(d, path)

    # Serve file if it exists
    if os.path.exists(requested) and os.path.isfile(requested):
        return FileResponse(requested)

    # SPA fallback
    return FileResponse(get_index_html())


@frontend.get("/app")
async def app_root():
    return RedirectResponse("/app/")


@frontend.get("/assets/{path:path}")
async def serve_assets(path: str, user=Depends(get_current_user)):
    d = detect_frontend_dir()
    if not d:
        raise HTTPException(500, "Frontend build not found")

    requested = os.path.join(d, "assets", path)
    if not os.path.exists(requested):
        raise HTTPException(404)

    return FileResponse(requested)


app.include_router(frontend)


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

RATE_LIMIT_SECONDS = 3


# ------------------------------------------------------
# Graph Context Tracking + WebSocket registry (NEW)
# ------------------------------------------------------

# Map concrete node IDs to "subnode names" as used for LLM routing
SUBNODE_MAP = {
    2: "Best practices",
    3: "Target groups",
    4: "Strategic overview",
}
SUBNODES = list(SUBNODE_MAP.values())

# Per-user graph/LLM context
user_graph_contexts: DefaultDict[str, dict] = defaultdict(
    lambda: {
        "selected_subnode": None,   # None = root (node 1), otherwise one of SUBNODES
        "latest_question": None,
        "latest_keywords": [],
        "prefetched": {},           # { subnode_name: llm_answer }
        "pending": {},              # { subnode_name: asyncio.Task }
    }
)

# Keep track of active websockets so background tasks can push messages into chat
active_websockets: dict[str, Optional[WebSocket]] = {}


async def push_chat_message(user_id: str, text: str):
    """
    Push an assistant-style message into the user's chat over WebSocket,
    if there is an active connection.
    """
    ws = active_websockets.get(user_id)
    if not ws:
        return

    try:
        # Stream as a single "message" + "done" pair
        await ws.send_json({
            "type": "message",
            "role": "chatbot",
            "content": text,
        })
        await ws.send_json({
            "type": "done",
            "full_response": text,
        })
    except Exception as e:
        # If sending fails, we just drop it; connection may have closed
        print(f"Failed to push chat message for user {user_id}: {e}")



async def prefetch_subnode(user_id: str, question: str, subnode: str):
    """
    Prefetch using /ask.
    The ONLY keywords passed are the 3 subnodes joined with OR.
    Subnode DOES NOT appear in the LLM prompt.
    """
    try:
        keywords = subnode

        synthetic_prompt = (
            "SYSTEM META-INSTRUCTION:\n"
            "If relevant, use the `paper_search` MCP tool to identify scientific "
            "literature or studies relevant to the question.\n\n"
            "Don't alter question and keywords below, insert them straight into tool\n"
            f"full_question:\n\"{question}\"\n\n"
            f"keywords_related_to_question=\"{keywords}\" "
            "Provide an evidence-informed explanation when possible.\n"
        )

        async with httpx.AsyncClient(timeout=httpx.Timeout(200)) as client:
            resp = await client.post(
                f"{WORKER_URL}/ask",
                json={
                    "chat_id": "prefetch",
                    "message": synthetic_prompt,
                }
            )

        resp.raise_for_status()
        answer = resp.json().get("llm", "")

        ctx = user_graph_contexts[user_id]
        ctx["prefetched"][subnode] = answer

        # If user is currently viewing this subnode, push to chat now
        if ctx["selected_subnode"] == subnode:
            await push_chat_message(user_id, answer)

    except Exception as e:
        print(f"Prefetch failed for {subnode}: {e}")

    finally:
        user_graph_contexts[user_id]["pending"].pop(subnode, None)


# ------------------------------------------------------
# WebSocket Chat
# ------------------------------------------------------
@app.websocket("/ws/chat")
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
                    f"{WORKER_URL}/ask_stream",
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


# ------------------------------------------------------
# HTTP Chat Endpoint (unchanged, no prefetch here)
# ------------------------------------------------------
@app.post("/chats/{chat_id}/messages")
async def send_chat_message(chat_id: str, payload: ChatMessage, user=Depends(get_current_user)):

    user_id = user["sub"]

    # --- Rate limiting ---
    if time.time() - user_last_request[user_id] < RATE_LIMIT_SECONDS:
        return {"message": "You're sending messages too fast. Please wait a moment."}

    user_last_request[user_id] = time.time()

    session = user_sessions[user_id]

    # Add user message to history
    session["history"].append({
        "role": "user",
        "message": payload.message
    })

    async with user_locks[user_id]:
        async with httpx.AsyncClient(timeout=httpx.Timeout(120)) as client:
            resp = await client.post(
                f"{WORKER_URL}/ask",
                json={
                    "chat_id": chat_id,
                    "message": payload.message,
                    "history": session["history"],
                    "topic": session["last_topic"],
                    "user_id": user_id
                }
            )

        if resp.status_code != 200:
            raise HTTPException(500, "Worker failed to process question")

        worker_result = resp.json()

        # Store topic if available
        if "topic" in worker_result:
            session["last_topic"] = worker_result["topic"]

        # Add assistant message to history
        session["history"].append({
            "role": "assistant",
            "message": worker_result.get("llm", "")
        })

        return {
            "message": worker_result.get("llm", "")
        }


# ------------------------------------------------------
# Node Context Endpoint (selection + original behavior)
# ------------------------------------------------------
@app.post("/nodes/{node_id}/context", response_model=ContextResponse)
async def get_node_context(node_id: int, user=Depends(get_current_user)):
    """
    Existing endpoint used by the frontend on graph node click.

    NEW behavior:
    - Updates user_graph_contexts[user_id]["selected_subnode"]
    - If an LLM answer was already prefetched for that subnode,
      it is pushed into the chat over WebSocket.

    OLD behavior preserved:
    - Returns the KG node + neighbor context as before.
    """
    user_id = user["sub"]
    ctx = user_graph_contexts[user_id]

    # Track selection based on node_id
    if node_id == 1:
        ctx["selected_subnode"] = "root"

        # Push prefetched root message if available
        if "root" in ctx["prefetched"]:
            await push_chat_message(user_id, ctx["prefetched"]["root"])

    elif node_id in SUBNODE_MAP:
        selected = SUBNODE_MAP[node_id]
        ctx["selected_subnode"] = selected

        # If we already have a prefetched LLM answer for this subnode,
        # push it into the chat immediately.
        if selected in ctx["prefetched"]:
            await push_chat_message(user_id, ctx["prefetched"][selected])

    # --- Original KG context logic below ---

    if kg_data is None:
        return ContextResponse(
            message="Knowledge graph data not loaded",
            nodes=[],
            edges=[],
            sources=[],
            error="not_loaded"
        )

    # Get node
    node = kg_data.get_entity(node_id)
    if not node:
        return ContextResponse(
            message=f"Node '{node_id}' not found",
            nodes=[],
            edges=[],
            sources=[],
            error="not_found"
        )

    # Get all edges referencing this node
    edges = [
        rel for rel in kg_data.relations.values()
        if int(rel.sourceId) == node_id or int(rel.targetId) == node_id
    ]

    # Collect neighbor nodes
    neighbor_ids = {
        int(rel.sourceId) for rel in edges
    } | {
        int(rel.targetId) for rel in edges
    }

    neighbor_nodes = [
        kg_data.entities[nid] for nid in neighbor_ids if nid in kg_data.entities
    ]

    return ContextResponse(
        message=f"Context for node {node_id}",
        nodes=neighbor_nodes,
        edges=edges,
        sources=[],
        error=None
    )


# ------------------------------------------------------
# Root (Protected)
# ------------------------------------------------------
@app.get("/")
async def root(user=Depends(get_current_user)):
    if kg_data is None:
        return {
            "status": "error",
            "message": "Knowledge graph data not loaded",
            "version": "0.1.0",
        }

    return {
        "status": "ok",
        "user": user,
        "version": "0.1.0",
        "data": {
            "entities_count": len(kg_data.entities),
            "relations_count": len(kg_data.relations),
            "questions_count": len(kg_data.questions),
        },
    }
