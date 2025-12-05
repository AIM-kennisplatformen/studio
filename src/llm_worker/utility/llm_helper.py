from pydantic import BaseModel
from llm_worker.lib.llm import LlamaAdapter
from llm_worker.lib import ModelConfig, LLMClient, MCPToolLoader
from llm_worker.lib.schemagenerators import LlamaAdapter

from pathlib import Path
from loguru import logger


class WorkerQuery(BaseModel):
    chat_id: str
    message: str

adapter = LlamaAdapter

configfile = Path("config.toml").resolve()
if not configfile.exists():
    logger.error(f"Config file {configfile} does not exist!")
else:
    logger.info(f"Loading config from {configfile}")

config = ModelConfig.from_toml(configfile)


llm = LLMClient(config)
logger.info(f"Initialized LLM client: {llm}")


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


