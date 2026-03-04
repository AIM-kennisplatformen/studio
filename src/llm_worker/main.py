import os
import sys
import uvicorn

from fastapi import FastAPI
from loguru import logger

from .endpoints.ask import llm_worker_router


# =====================================================
# Logging
# =====================================================

logger.remove()
logger.add(sys.stderr, level="INFO")


# =====================================================
# FastAPI App
# =====================================================

app = FastAPI(
    title="Worker API",
    description="Runs LLM + MCP tools task processing",
    version="0.1.0",
)

app.include_router(llm_worker_router)


# =====================================================
# Local entrypoint (dev only)
# =====================================================

if __name__ == "__main__":
    port = int(os.getenv("LLM_WORKER_PORT", "9200"))

    logger.info(f"Starting worker on http://0.0.0.0:{port}")

    uvicorn.run(
        "llm_worker.main:app",
        host="0.0.0.0",
        port=port,
        reload=True,   # ⚠ dev only
    )
