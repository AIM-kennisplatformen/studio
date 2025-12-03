import json
import sys
from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from loguru import logger


# ---- Imports from your project ----
from lib import ModelConfig, LLMClient, MCPToolLoader
from lib.schemagenerators import LlamaAdapter


logger.remove()
logger.add(sys.stderr, level="INFO")


# ------------------------------------------------------------
# FASTAPI APP
# ------------------------------------------------------------
app = FastAPI(
    title="Worker API",
    description="Runs LLM + MCP tools task processing",
    version="0.1.0"
)


# ------------------------------------------------------------
# LOAD CONFIG
# ------------------------------------------------------------
configfile = Path("config.toml").resolve()
if not configfile.exists():
    logger.error(f"Config file {configfile} does not exist!")
else:
    logger.info(f"Loading config from {configfile}")

config = ModelConfig.from_toml(configfile)


# ------------------------------------------------------------
# INITIALIZE LLM
# ------------------------------------------------------------
llm = LLMClient(config)
logger.info(f"Initialized LLM client: {llm}")


# ------------------------------------------------------------
# INITIALIZE MCP TOOL LOADER
# ------------------------------------------------------------
loader = MCPToolLoader()
tool_collection = None


async def load_tools_once():
    """Load MCP tools only once at startup."""
    global tool_collection
    if tool_collection is None:
        logger.info("Loading MCP tools via SSE…")
        tool_collection = await loader.load_server(
            name="paper_search",
            target="http://localhost:8000/sse",
        )
        logger.info(f"Loaded {len(tool_collection)} tools via SSE")


@app.on_event("startup")
async def startup_event():
    await load_tools_once()


# ------------------------------------------------------------
# SELECT ADAPTER
# ------------------------------------------------------------
adapter = LlamaAdapter

# ------------------------------------------------------------
# PIPELINE FUNCTION (LLM ONLY)
# ------------------------------------------------------------
async def run_pipeline(user_query: str):
    """
    Runs:
        1. LLM Query
        2. Returns result (NO KG CLIENT)
    """
    logger.info(f"Running pipeline for query: {user_query}")

    messages = [{"role": "user", "content": user_query}]
    response = await llm(messages)
    llm_content = adapter.get_content(response)

    return {
        "llm": llm_content,
        "tools": f"{len(tool_collection)} tools available"
    }


# ------------------------------------------------------------
# WORKER API ENDPOINT
# ------------------------------------------------------------
class WorkerQuery(BaseModel):
    chat_id: str
    message: str


@app.post("/ask")
async def ask_worker(payload: WorkerQuery):
    result = await run_pipeline(payload.message)
    return result

@app.post("/ask_stream")
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

# ------------------------------------------------------------
# LOCAL DEVELOPMENT ENTRYPOINT
# ------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    print("Starting Worker on http://localhost:7000")
    uvicorn.run("llm_worker.main:app", host="0.0.0.0", port=7000, reload=True)
