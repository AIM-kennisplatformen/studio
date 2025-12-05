from utility.llm_helper import run_pipeline, WorkerQuery, load_tools_once

from loguru import logger
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
import json

llm_worker_router = APIRouter()

@llm_worker_router.post("/ask")
async def ask_worker(payload: WorkerQuery):
    result = await run_pipeline(payload.message)
    return result

@llm_worker_router.post("/ask_stream")
async def ask_worker_stream(payload: WorkerQuery):
    """
    Streaming NDJSON endpoint (fake streaming).

    It:
      1. Runs the normal pipeline (LLM + tools) to completion.
      2. Streams the final answer in chunks as {"token": "..."} lines.
      3. Finishes with {"done": true, "full_response": "...", "tools": "..."}.
    """
    user_query = payload.message
    logger.info(f"Fake-streaming pipeline for query: {user_query}")

    async def event_stream():
        # 1. Run the original pipeline once (same as /ask)
        result = await run_pipeline(user_query)
        full = result["llm"]
        tools_info = result.get("tools")

        # 2. Stream out in chunks
        chunk_size = 64  # tweak to taste (chars per chunk)
        for i in range(0, len(full), chunk_size):
            tok = full[i:i + chunk_size]
            yield json.dumps({"token": tok}) + "\n"

        # 3. Final "done" event with full response + tool info
        yield json.dumps({
            "done": True,
            "full_response": full,
            "tools": tools_info,
        }) + "\n"

    return StreamingResponse(
        event_stream(),
        media_type="application/json",
    )
