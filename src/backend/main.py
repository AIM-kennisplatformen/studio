from fastapi import FastAPI
from contextlib import asynccontextmanager

from backend.config import config
from starlette.middleware.sessions import SessionMiddleware
from fastapi.middleware.cors import CORSMiddleware

from backend.utility.graph_data_loader import load_knowledge_graph
from backend.endpoints.assets import asset_router, frontend, detect_frontend_dir
from backend.endpoints.auth import auth_router
from backend.endpoints.chat import chat_router, socket_app
from backend.endpoints.graph import graph_router
from backend.endpoints.log_event import log_event_router
from backend.stores.redis import redis_store

# Build list of allowed CORS origins
cors_origins = [config["base_url"]]

@asynccontextmanager
async def lifespan(app: FastAPI):
    kg_data = load_knowledge_graph()
    app.state.kg_data = kg_data

    print(f"✓ Loaded {len(kg_data.entities)} entities")
    print(f"✓ Loaded {len(kg_data.relations)} relations")
    print(f"✓ Loaded {len(kg_data.questions)} questions")
    print(f"✓ Frontend directory detected: {detect_frontend_dir()}")

    await redis_store.connect()

    yield
    
    await redis_store.close()

app = FastAPI(
    title="Knowledge Graph API",
    description="API for chat-based knowledge graph generation and node context retrieval",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    SessionMiddleware,
    secret_key=config["session_secret"],
    same_site="lax",        # REQUIRED for cross-site requests
    https_only=False,        # Only True if you deploy with HTTPS
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/socket.io", socket_app)
app.include_router(asset_router)
app.include_router(auth_router)
app.include_router(chat_router)
app.include_router(graph_router)
app.include_router(log_event_router)
app.include_router(frontend)
