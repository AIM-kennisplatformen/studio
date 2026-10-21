from fastapi import FastAPI
from contextlib import asynccontextmanager

from src.config import config
from starlette.middleware.sessions import SessionMiddleware

from src.utility.graph_data_loader import load_knowledge_graph
from src.endpoints.assets import asset_router
from src.endpoints.auth import auth_router
from src.endpoints.chat import chat_router, socket_app
from src.endpoints.graph import graph_router
from src.endpoints.log_event import log_event_router
from src.endpoints.sessions import sessions_router
from src.endpoints.settings import settings_router
from src.stores.postgres import postgres_store
from src.stores.redis import redis_store

@asynccontextmanager
async def lifespan(app: FastAPI):
    kg_data = load_knowledge_graph()
    app.state.kg_data = kg_data

    print(f"✓ Loaded {len(kg_data.entities)} entities")
    print(f"✓ Loaded {len(kg_data.relations)} relations")
    print(f"✓ Loaded {len(kg_data.questions)} questions")
    await redis_store.connect({
        "redis_url": config["redis_url"],
        "redis_expiration_time": config["redis_expiration_time"]
    })
    await postgres_store.connect({
        "postgres_url": config["postgres_url"],
    })
    yield

    await postgres_store.close()
    await redis_store.close()

app = FastAPI(
    title="Knowledge Graph API",
    description="API for chat-based knowledge graph generation and node context retrieval",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
    redoc_url="/api/redoc",
    swagger_ui_oauth2_redirect_url="/api/docs/oauth2-redirect",
)

app.add_middleware(
    SessionMiddleware,
    secret_key=config["session_secret"],
    same_site="lax",        # REQUIRED for cross-site requests
    https_only=False,        # Only True if you deploy with HTTPS
)

app.mount("/api/socket.io", socket_app)
app.include_router(asset_router, prefix="/api")
app.include_router(auth_router, prefix="/api")
app.include_router(chat_router, prefix="/api")
app.include_router(graph_router, prefix="/api")
app.include_router(log_event_router, prefix="/api")
app.include_router(sessions_router, prefix="/api")
app.include_router(settings_router, prefix="/api")
