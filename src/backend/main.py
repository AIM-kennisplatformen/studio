from fastapi import FastAPI
from backend.config import SESSION_SECRET
from starlette.middleware.sessions import SessionMiddleware
from fastapi.middleware.cors import CORSMiddleware

from backend.endpoints.assets import asset_router, frontend
from backend.endpoints.auth import auth_router
from backend.endpoints.chat import chat_router
from backend.endpoints.graph import graph_router
from backend.endpoints.startup import router



app = FastAPI(
    title="Knowledge Graph API",
    description="API for chat-based knowledge graph generation and node context retrieval",
    version="0.1.0"
)

app.add_middleware(SessionMiddleware, secret_key=SESSION_SECRET)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:10090"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(asset_router)
app.include_router(auth_router)
app.include_router(chat_router)
app.include_router(graph_router)
app.include_router(router)
app.include_router(frontend)