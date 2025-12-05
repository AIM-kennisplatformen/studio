import re
import tomllib
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

configfile = Path("llm_worker_config.toml").resolve()
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
        with configfile.open("rb") as f:
            llm_secton = tomllib.load(f)["llm"]
            
            tool_collection = await loader.load_server(
                name="paper_search",
                target=llm_secton["mcp_server"],
            )
        logger.info(f"Loaded {len(tool_collection)} tools via SSE")

def sanitize_output(text: str) -> str:
    # Remove chain-of-thought markers
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)

    # Remove any stray reasoning tags
    text = re.sub(r"<.*?reason.*?>.*?</.*?reason.*?>", "", text, flags=re.DOTALL)

    # Trim excessive whitespace
    return text.strip()

async def run_pipeline(user_query: str):
    """
    Runs:
        1. LLM Query
        2. Returns result (NO KG CLIENT)
    """
    logger.info(f"Running pipeline for query: {user_query}")

    messages = [{"role": "user", "content": user_query}]
    response = await llm(messages)
    llm_content = sanitize_output(adapter.get_content(response))

    return {
        "llm": llm_content,
        "tools": f"{len(tool_collection)} tools available"
    }


