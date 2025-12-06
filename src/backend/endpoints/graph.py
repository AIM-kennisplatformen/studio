from backend.utility.graph_api_models import ContextResponse
from src.backend.utility.chat_util import push_chat_message
from backend.endpoints.auth import get_current_user
from backend.config import LLM_WORKER_URL


from typing import DefaultDict
from collections import defaultdict
from fastapi import Depends, Request
import httpx
from fastapi import APIRouter

graph_router = APIRouter()

# Map concrete node IDs to "subnode names" as used for LLM routing
SUBNODE_MAP = {
    2: "Best practices",
    3: "Target groups",
    4: "Strategic overview",
}
SUBNODES = list(SUBNODE_MAP.values())

# Per-user graph/LLM context
user_graph_contexts: DefaultDict[str, dict] = defaultdict(
    lambda: {
        "selected_subnode": None,   # None = root (node 1), otherwise one of SUBNODES
        "latest_question": None,
        "latest_keywords": [],
        "prefetched": {},           # { subnode_name: llm_answer }
        "pending": {},              # { subnode_name: asyncio.Task }
    }
)


async def prefetch_subnode(user_id: str, question: str, subnode: str):
    """
    Prefetch using /ask.
    The ONLY keywords passed are the 3 subnodes joined with OR.
    Subnode DOES NOT appear in the LLM prompt.
    """
    try:
        keywords = subnode

        synthetic_prompt = (
            "SYSTEM META-INSTRUCTION:\n"
            "If relevant, use the `paper_search` MCP tool to identify scientific "
            "literature or studies relevant to the question.\n\n"
            "Don't alter question and keywords below, insert them straight into tool\n"
            f"full_question:\n\"{question}\"\n\n"
            f"keywords_related_to_question=\"{keywords}\" "
            "Provide an evidence-informed explanation when possible.\n"
        )

        async with httpx.AsyncClient(timeout=httpx.Timeout(200)) as client:
            resp = await client.post(
                f"{LLM_WORKER_URL}/ask",
                json={
                    "chat_id": "prefetch",
                    "message": synthetic_prompt,
                }
            )

        resp.raise_for_status()
        answer = resp.json().get("llm", "")

        ctx = user_graph_contexts[user_id]
        ctx["prefetched"][subnode] = answer

        # If user is currently viewing this subnode, push to chat now
        if ctx["selected_subnode"] == subnode:
            await push_chat_message(user_id, answer)

    except Exception as e:
        print(f"Prefetch failed for {subnode}: {e}")

    finally:
        user_graph_contexts[user_id]["pending"].pop(subnode, None)




# ------------------------------------------------------
# Node Context Endpoint (selection + original behavior)
# ------------------------------------------------------
@graph_router.post("/nodes/{node_id}/context")
async def get_node_context(node_id: int, request: Request, user=Depends(get_current_user)):
    """
    Existing endpoint used by the frontend on graph node click.

    NEW behavior:
    - Updates user_graph_contexts[user_id]["selected_subnode"]
    - If an LLM answer was already prefetched for that subnode,
      it is pushed into the chat over WebSocket.

    OLD behavior preserved:
    - Returns the KG node + neighbor context as before.
    """
    user_id = user["sub"]
    ctx = user_graph_contexts[user_id]
    kg_data = request.app.state.kg_data
    # Track selection based on node_id
    if node_id == 1:
        ctx["selected_subnode"] = "root"

        # Push prefetched root message if available
        if "root" in ctx["prefetched"]:
            await push_chat_message(user_id, ctx["prefetched"]["root"])

    elif node_id in SUBNODE_MAP:
        selected = SUBNODE_MAP[node_id]
        ctx["selected_subnode"] = selected

        # If we already have a prefetched LLM answer for this subnode,
        # push it into the chat immediately.
        if selected in ctx["prefetched"]:
            await push_chat_message(user_id, ctx["prefetched"][selected])

    # --- Original KG context logic below ---

    if kg_data is None:
        return ContextResponse(
            message="Knowledge graph data not loaded",
            nodes=[],
            edges=[],
            sources=[],
            error="not_loaded"
        )

    # Get node
    node = kg_data.get_entity(node_id)
    if not node:
        return ContextResponse(
            message=f"Node '{node_id}' not found",
            nodes=[],
            edges=[],
            sources=[],
            error="not_found"
        )

    # Get all edges referencing this node
    edges = [
        rel for rel in kg_data.relations.values()
        if int(rel.sourceId) == node_id or int(rel.targetId) == node_id
    ]

    # Collect neighbor nodes
    neighbor_ids = {
        int(rel.sourceId) for rel in edges
    } | {
        int(rel.targetId) for rel in edges
    }

    neighbor_nodes = [
        kg_data.entities[nid] for nid in neighbor_ids if nid in kg_data.entities
    ]

    return ContextResponse(
        message=f"Context for node {node_id}",
        nodes=neighbor_nodes,
        edges=edges,
        sources=[],
        error=None
    )


