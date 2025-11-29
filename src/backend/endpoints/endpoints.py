from fastapi import FastAPI, HTTPException, Request, Depends, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, FileResponse
from starlette.middleware.sessions import SessionMiddleware

from pydantic import BaseModel
from typing import Optional
import os
import random

from authlib.integrations.starlette_client import OAuth

from .models import Node, Edge, Source, ChatResponse, ContextResponse
from .data_loader import load_knowledge_graph, KnowledgeGraphData


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
BASE_URL = os.getenv("BASE_URL", "http://kg.localhost")
DISCOVERY_URL = os.getenv("OAUTH_DISCOVERY_URL")
CLIENT_ID = os.getenv("OAUTH_CLIENT_ID")
CLIENT_SECRET = os.getenv("OAUTH_CLIENT_SECRET")

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
    allow_origins=["*"],  # restrict in prod
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

def detect_frontend_dir():
    """
    Detect a folder that contains BOTH index.html AND assets/ folder.
    This is required for Vite/React/Vue/etc.
    """
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
# API Routes (Protected)
# ------------------------------------------------------
class ChatMessage(BaseModel):
    message: str


@app.post("/chats/{chat_id}/messages", response_model=ChatResponse)
async def send_chat_message(chat_id: str, payload: ChatMessage, user=Depends(get_current_user)):
    if kg_data is None:
        return ChatResponse(
            message="",
            nodes=[],
            edges=[],
            sources=[],
            error="Knowledge graph data not loaded",
        )

    if not kg_data.questions:
        return ChatResponse(
            message="",
            nodes=[],
            edges=[],
            sources=[],
            error="No questions available",
        )

    question = random.choice(kg_data.questions)
    answer = question.get("answer", "")

    nodes = [kg_data.get_entity(e) for e in question.get("entities", []) if kg_data.get_entity(e)]
    edges = [kg_data.get_relation(r) for r in question.get("relations", []) if kg_data.get_relation(r)]

    return ChatResponse(message=answer, nodes=nodes, edges=edges, sources=[], error=None)


@app.get("/nodes/{node_id}/context", response_model=ContextResponse)
async def get_node_context(node_id: str, user=Depends(get_current_user)):
    return ContextResponse(
        message="",
        nodes=[],
        edges=[],
        sources=[],
        error="Not implemented yet",
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
