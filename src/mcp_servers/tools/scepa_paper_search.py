from langfuse import observe
from mcp.server.fastmcp import FastMCP

from mcp_servers.lib.qdrant.qdrant_source import QdrantSource
from mcp_servers.lib.zotero.zotero_source import ZoteroSource
from dotenv import load_dotenv
import os

# -------------------------------
# MCP server init
# -------------------------------
mcp = FastMCP("paper_search")

zotero_source = ZoteroSource()

load_dotenv()
qdrant_source = QdrantSource(os.getenv("QDRANT_URL","127.0.0.1"), os.getenv("QDRANT_PORT",6333), "knowledgeplatform")


@mcp.tool()
@observe(name="get_literature_supported_knowledge_sources")
async def get_literature_supported_knowledge(
    full_question: str, keywords_related_to_question: str
) -> str:
    """
    Geef een menselijk leesbare samenvatting van relevante literatuur
    waarin Zotero-titels worden gekoppeld aan Qdrant-resultaten.
    """
    print("tool_call, full_question: "+full_question+" keywords: "+keywords_related_to_question)
    # 1. Haal Zotero metadata op
    related_sources = await zotero_source.extract_zotero_metadata(
        query=keywords_related_to_question
    )

    if not related_sources:
        return (
            "Geen relevante literatuur gevonden op basis van de opgegeven zoekwoorden."
        )

    # 2. Verzamel Zotero keys (hashes)
    hashes = [s.get("key") for s in related_sources if "key" in s]
    if not hashes:
        return "Geen geldige Zotero-referenties gevonden."

    # 3. Maak lookup tabel: {hash -> title}
    title_lookup = {
        src["key"]: src["data"].get("title", "Onbekende titel")
        for src in related_sources
        if "key" in src and "data" in src
    }

    # 4. Query Qdrant
    qdrant_results = qdrant_source.query_on_subset(full_question, hashes)

    if not qdrant_results:
        return "Er zijn geen relevante tekstfragmenten gevonden in de kennisbank."

    # 5. Bouw nette samenvatting
    lines = ["Relevante gevonden literatuur:\n"]

    for item in qdrant_results:
        hash_key = item.get("zotero_hash")
        title = title_lookup.get(hash_key, "Onbekende titel")
        score = item.get("score", 0)
        snippet = item.get("text", "").strip()

        # Snippet inkorten
        if len(snippet) > 500:
            snippet = snippet[:500].rsplit(" ", 1)[0] + "..."

        lines.append(f"— Score {score:.2f}\n  Titel: {title}\n  Bron: {snippet}\n")

    return "\n".join(lines)
