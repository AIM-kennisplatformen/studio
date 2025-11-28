from lib import ModelConfig, ClientType, LLMClient, MCPToolLoader
from lib.schemagenerators import AnthropicAdapter, LlamaAdapter
from endpoints.kg_client import KnowledgeGraphClient        # <-- add this
from pathlib import Path
from loguru import logger
import sys
import asyncio


logger.remove()
logger.add(sys.stderr, level="INFO")


async def main():
    # ---- Load MCP Tools ----
    loader = MCPToolLoader()
    collection = await loader.load_server(
        name="paper_search",
        target="http://localhost:8000/sse",
    )
    logger.info(f"Loaded {len(collection)} tools via SSE")

    # ---- Load Config ----
    configfile = Path("config.toml").resolve()
    if not configfile.exists():
        logger.error(f"Config file {configfile} does not exist!")
    logger.info(f"Loading config from {configfile}")

    config = ModelConfig.from_toml(configfile)

    # ---- Initialize LLM ----
    llm = LLMClient(config)
    logger.info(f"Initialized LLM client: {llm}")

    # ---- Initialize Knowledge Graph Client ----
    kg = KnowledgeGraphClient(base_url="http://localhost:9000")
    logger.info("Knowledge Graph client initialized")

    queries = [
        'full question: "effect of subsidies on rural side energy poverty" keywords: "Best practices" use the tool call.'
    ]

    adapter = AnthropicAdapter
    if config.client_type == ClientType.OLLAMA:
        adapter = LlamaAdapter

    for i, query in enumerate(queries):
        logger.info(f"User Query: {query}")

        # -------------------------
        # 1. Ask LLM
        # -------------------------
        messages = [{"role": "user", "content": query}]
        response = await llm(messages)
        content = adapter.get_content(response)
        logger.info(f"LLM response: \n{content}")

        # -------------------------
        # 2. Ask Knowledge Graph
        # -------------------------
        kg_resp = await kg.ask(chat_id="session-1", message=query)
        logger.info(f"KG response: \n{kg_resp}")

        # -------------------------
        # 3. Combine or store results as needed
        # -------------------------
        logger.info("Combined Result:")
        logger.info({
            "llm": content,
            "kg": kg_resp
        })


if __name__ == "__main__":
    asyncio.run(main())
