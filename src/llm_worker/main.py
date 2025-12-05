from utility.llm_helper import load_tools_once
from endpoints.ask import llm_worker_router

from contextlib import asynccontextmanager
import sys
from fastapi import FastAPI
from loguru import logger

logger.remove()
logger.add(sys.stderr, level="INFO")

app = FastAPI(
    title="Worker API",
    description="Runs LLM + MCP tools task processing",
    version="0.1.0"
)
app.include_router(llm_worker_router)

@asynccontextmanager
async def lifespan(app: FastAPI):
    await load_tools_once()  # runs on startup
    yield
    # Any shutdown logic goes here

if __name__ == "__main__":
    import uvicorn
    print("Starting Worker on http://localhost:7000")
    uvicorn.run("llm_worker.main:app", host="0.0.0.0", port=7000, reload=True)
