from typing import Dict, Any
from mcp.server.fastmcp import FastMCP
from langfuse import Langfuse, observe
from studio.zotero.zotero_source import ZoteroSource
from studio.qdrant.qdrant_source import QdrantSource

# -------------------------------
# MCP server init
# -------------------------------
mcp = FastMCP("paper_search")

langfuse = Langfuse(
  secret_key="dev-secret-key", # change in production
  public_key="dev-public-key", # change in production
  host="http://host.docker.internal:3000" # change in production
)

zotero_source = ZoteroSource()
qdrant_source = QdrantSource("127.0.0.1", 6333, "knowledgeplatform")


@mcp.tool()
@observe(name="get_more_information_about_literature")
async def get_more_information_about_literature() -> str:
    """Summarizes the key literature topics in the energy politics corpus."""
    papers = zotero_source.list_all_items(limit=50)
    if not papers:
        return "No literature found in the Zotero library."
    topics = zotero_source.extract_topics(papers)
    return f"The current literature collection includes research on {', '.join(topics)}."

@mcp.tool()
@observe(name="get_literature_supported_knowledge_sources")
async def get_literature_supported_knowledge(full_question: str, keywords_related_to_question: str) -> list[Dict[str, Any]]:
    """Return citations from papers stored in the knowledge set based on question and related keywords."""
    related_sources = zotero_source.extract_zotero_metadata(keywords_related_to_question)
    if not related_sources:
        return [{"message": "No related sources found for the given keywords."}]

    hashes = [s["hash"] for s in related_sources if "hash" in s]
    if not hashes:
        return [{"message": "No valid hashes found in Zotero metadata."}]

    qdrant_sources = qdrant_source.query_on_subset(full_question, hashes)
    return qdrant_sources or [{"message": "No relevant literature found in Qdrant."}]