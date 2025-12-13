from typing import DefaultDict, Dict, Any
from collections import defaultdict

import httpx
from fastapi import APIRouter, Depends, Request

from backend.utility.graph_api_models import ContextResponse
from backend.endpoints.auth import get_current_user
from backend.config import LLM_WORKER_URL, LLM_WORKER_PORT

from src.backend.utility.chat_util import push_chat_message


graph_router = APIRouter()


# =====================================================
# Subnode Mapping
# =====================================================

SUBNODE_MAP = {
    2: "Best practices",
    3: "Target groups",
    4: "Strategic overview",
}

SUBNODES = list(SUBNODE_MAP.values())


# =====================================================
# Per-user Graph Context
# =====================================================

def _default_user_graph_context() -> Dict[str, Any]:
    return {
        "selected_subnode": "root",
        "latest_question": None,
        "latest_keywords": [],
        "prefetched": {},   # subnode_name → llm_answer
        "pending": {},      # subnode_name → asyncio.Task
    }

user_graph_contexts: DefaultDict[str, Dict[str, Any]] = defaultdict(
    _default_user_graph_context
)


# =====================================================
# Prefetch Logic
# =====================================================

async def prefetch_subnode(user_id: str, question: str, subnode: str):
    """
    Prefetches a subnode answer from the LLM worker.
    - Saves result to user_graph_contexts[user_id]["prefetched"]
    - If the user is viewing that subnode, pushes it immediately.
    """
    ctx = user_graph_contexts[user_id]

    try:
        # Build prefetch prompt
        prompt = (
            "SYSTEM META-INSTRUCTION:\n"
            "If relevant, use the `paper_search` MCP tool to identify scientific "
            "literature or studies relevant to the question.\n\n"
            "Don't alter question and keywords below — insert them straight into the tool.\n"
            f"full_question:\n\"{question}\"\n\n"
            f"keywords_related_to_question=\"{subnode}\" "
            "Provide an evidence-informed explanation when possible.\n"
        )

        async with httpx.AsyncClient(timeout=200) as client:
            worker_url = f"{LLM_WORKER_URL}:{LLM_WORKER_PORT}"
            resp = await client.post(
                f"{worker_url}/ask",
                json={"chat_id": "prefetch", "message": prompt},
            )

        resp.raise_for_status()
        answer = resp.json().get("llm", "")

        # Store prefetch result
        ctx["prefetched"][subnode] = answer

        # Auto-push if user is viewing this subnode
        if ctx["selected_subnode"] == subnode:
            await push_chat_message(user_id, answer)

    except Exception as e:
        print(f"[PREFETCH ERROR - {subnode}] {e}")

    finally:
        # Clean up pending entry
        ctx["pending"].pop(subnode, None)


# =====================================================
# Graph Node Selection Endpoint
# =====================================================

@graph_router.post("/nodes/{node_id}/context")
async def get_node_context(
    node_id: int,
    request: Request,
    user=Depends(get_current_user),
):
    """
    User clicked a graph node. This:
    - updates the user's selected subnode
    - pushes prefetch results if available
    - returns standard KG node context to frontend
    """
    user_id = user["sub"]
    ctx = user_graph_contexts[user_id]
    kg_data = request.app.state.kg_data

    # --------------------------------------------------
    # ROOT NODE SELECTED
    # --------------------------------------------------
    if node_id == 1:
        ctx["selected_subnode"] = "root"

        if "root" in ctx["prefetched"]:
            await push_chat_message(user_id, ctx["prefetched"]["root"])

    # --------------------------------------------------
    # SUBNODE SELECTED
    # --------------------------------------------------
    elif node_id in SUBNODE_MAP:
        subnode = SUBNODE_MAP[node_id]
        ctx["selected_subnode"] = subnode

        # Push cached prefetch result immediately
        prefetched_answer = ctx["prefetched"].get(subnode)
        if prefetched_answer:
            await push_chat_message(user_id, prefetched_answer)

    # --------------------------------------------------
    # Knowledge Graph Lookup
    # --------------------------------------------------
    if kg_data is None:
        return ContextResponse(
            message="Knowledge graph data not loaded",
            nodes=[],
            edges=[],
            sources=[],
            error="not_loaded",
        )

    node = kg_data.get_entity(node_id)
    if not node:
        return ContextResponse(
            message=f"Node '{node_id}' not found",
            nodes=[],
            edges=[],
            sources=[],
            error="not_found",
        )

    # Gather edges involving this node
    edges = [
        rel for rel in kg_data.relations.values()
        if int(rel.sourceId) == node_id or int(rel.targetId) == node_id
    ]

    # Gather neighbor nodes
    neighbor_ids = (
        {int(rel.sourceId) for rel in edges} |
        {int(rel.targetId) for rel in edges}
    )

    neighbor_nodes = [
        kg_data.entities[nid] for nid in neighbor_ids
        if nid in kg_data.entities
    ]

    return ContextResponse(
        message=f"Context for node {node_id}",
        nodes=neighbor_nodes,
        edges=edges,
        sources=[],
        error=None,
    )
