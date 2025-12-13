import json
import os
import time
from typing import AsyncGenerator

from dotenv import load_dotenv
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from langchain_openai import ChatOpenAI
from langfuse import Langfuse, get_client
from langfuse.langchain import CallbackHandler
from mcp_use import MCPAgent, MCPClient
from pydantic import BaseModel
from mcp_use.client.config import load_config_file

# =====================================================
# Environment & Langfuse
# =====================================================

load_dotenv()

Langfuse(
    public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
    secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
    host=os.getenv("LANGFUSE_HOST"),
)

# =====================================================
# Models
# =====================================================

class WorkerQuery(BaseModel):
    chat_id: str
    message: str


# =====================================================
# Agent Factory
# =====================================================

async def create_agent() -> MCPAgent:
    config = load_config_file(os.getenv("MCP_TOOL_CONFIG_PATH"))

    client = MCPClient(config)

    llm = ChatOpenAI(
        model=os.getenv("LLM_MODEL"),
        base_url=os.getenv("OPENAI_HOST"),
    )

    return MCPAgent(
        llm=llm,
        client=client,
        max_steps=30,
        callbacks=[CallbackHandler()],
    )


# =====================================================
# Router
# =====================================================

llm_worker_router = APIRouter()


# =====================================================
# Non-streaming endpoint
# =====================================================

@llm_worker_router.post("/ask")
async def ask_worker(payload: WorkerQuery):
    langfuse = get_client()
    agent = await create_agent()

    try:
        result = await agent.run(payload.message)
        return {
            "llm": result,
            "tools": "1 tools available",
        }
    finally:
        langfuse.flush()


# =====================================================
# Streaming endpoint (SSE)
# =====================================================

@llm_worker_router.post("/ask_stream")
async def ask_worker_stream(payload: WorkerQuery):
    langfuse = get_client()

    async def event_generator() -> AsyncGenerator[str, None]:
        agent = await create_agent()

        try:
            async for event in agent.stream_events(payload.message):
                event_type = event.get("event")

                data = ""
                if event_type == "on_chat_model_stream":
                    data = event["data"]["chunk"].content or ""

                sse_payload = {
                    "type": event_type,
                    "timestamp": time.time(),
                    "data": data,
                }

                yield f"data: {json.dumps(sse_payload)}\n\n"

            yield "data: [DONE]\n\n"

        finally:
            langfuse.flush()

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream", 
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )
