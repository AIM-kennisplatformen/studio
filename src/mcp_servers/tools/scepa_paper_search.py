from langfuse import observe
from mcp.server.fastmcp import FastMCP

from mcp_servers.lib.qdrant.qdrant_source import QdrantSource
from mcp_servers.lib.zotero.zotero_source import ZoteroSource
from dotenv import load_dotenv
import os

# -------------------------------
# MCP server initialization
# -------------------------------
mcp = FastMCP("paper_search")

zotero_source = ZoteroSource()

load_dotenv()
qdrant_source = QdrantSource(
    os.getenv("QDRANT_URL", "127.0.0.1"),
    os.getenv("QDRANT_PORT", 6333),
    "knowledgeplatform",
)


@mcp.tool()
@observe(name="get_literature_supported_knowledge_sources")
async def get_literature_supported_knowledge(
    full_question: str, keywords_related_to_question: str
) -> str:
    """
    Provide a human-readable summary of relevant literature
    in which Zotero titles are linked to Qdrant results.
    """
    print(
        "tool_call, full_question: "
        + full_question
        + " keywords: "
        + keywords_related_to_question
    )

    # 1. Retrieve Zotero metadata
    related_sources = await zotero_source.extract_zotero_metadata(
        query=keywords_related_to_question
    )

    if not related_sources:
        return (
            "No relevant literature was found based on the provided keywords."
        )

    # 2. Collect Zotero keys (hashes)
    hashes = [s.get("key") for s in related_sources if "key" in s]
    if not hashes:
        return "No valid Zotero references were found."

    # 3. Create lookup table: {hash -> title}
    title_lookup = {
        src["key"]: src["data"].get("title", "Unknown title")
        for src in related_sources
        if "key" in src and "data" in src
    }

    # 4. Query Qdrant
    qdrant_results = qdrant_source.query_on_subset(full_question, hashes)

    if not qdrant_results:
        return "No relevant text fragments were found in the knowledge base."

    # 5. Build a clean summary
    lines = ["Relevant literature found:\n"]

    for item in qdrant_results:
        hash_key = item.get("zotero_hash")
        title = title_lookup.get(hash_key, "Unknown title")
        score = item.get("score", 0)
        snippet = item.get("text", "").strip()

        # Truncate snippet if too long
        if len(snippet) > 500:
            snippet = snippet[:500].rsplit(" ", 1)[0] + "..."

        lines.append(
            f"— Score {score:.2f}\n"
            f"  Title: {title}\n"
            f"  Source: {snippet}\n"
        )

    return "\n".join(lines)
