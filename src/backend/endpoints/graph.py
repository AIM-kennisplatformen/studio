from typing import DefaultDict, Dict, Any
from collections import defaultdict

import httpx
from fastapi import APIRouter, Depends, Request

from backend.utility.graph_api_models import ContextResponse
from backend.endpoints.auth import get_current_user
from backend.config import LLM_WORKER_URL, LLM_WORKER_PORT

from src.backend.utility.chat_util import push_chat_message, push_chat_message_stream
import json
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

def strip_think(text: str) -> str:
    while True:
        start = text.find("<think>")
        if start == -1:
            break
        end = text.find("</think>", start)
        if end == -1:
            text = text[:start]
            break
        text = text[:start] + text[end + len("</think>"):]
    return text.strip()


# =====================================================
# Per-user Graph Context
# =====================================================

def _default_user_graph_context() -> Dict[str, Any]:
    return {
        "selected_subnode": "root",
        "latest_question": None,
        "previous_question": None,
        "latest_keywords": [],
        "prefetched": {},   # subnode_name → llm_answer
        "pending": {},      # subnode_name → asyncio.Task
        "dialogue_state_asked": False,
    }

user_graph_contexts: DefaultDict[str, Dict[str, Any]] = defaultdict(
    _default_user_graph_context
)


# =====================================================
# Prefetch Logic
# =====================================================

async def fetch_subnode_stream(user_id: str, question: str, subnode: str):
    """
    Docstring for fetch_subnode_stream
    
    :param user_id: Description
    :type user_id: str
    :param question: Description
    :type question: str
    :param subnode: Description
    :type subnode: str
    """
    ctx = user_graph_contexts[user_id]

    try:
        if subnode == "root":
            subnode = "Best practices || Target groups || Strategic overview"
        synthetic_prompt = (
            "SYSTEM META-INSTRUCTION:\n"
            "If relevant, use the `paper_search` MCP tool to identify scientific "
            "literature or studies relevant to the question.\n\n"
            "Don't alter question and keywords below — insert them straight into the tool.\n"
            f"full_question:\n\"{question}\"\n\n"
            f"keywords_related_to_question=\"{subnode}\" "
            "Provide an evidence-informed explanation when possible.\n"
        )

        worker_url = f"{LLM_WORKER_URL}:{LLM_WORKER_PORT}"
        full_response = ""

        async with httpx.AsyncClient(timeout=None) as client:
            async with client.stream(
                "POST",
                f"{worker_url}/ask_stream",
                json={
                    "chat_id": "default",
                    "message": synthetic_prompt,
                    "user_id": user_id,
                },
            ) as resp:
                async for line in resp.aiter_lines():
                    if not line.startswith("data:"):
                        continue

                    raw = line.removeprefix("data:").strip()

                    if raw == "[DONE]":
                        break

                    try:
                        payload = json.loads(raw)
                    except json.JSONDecodeError:
                        continue

                    event_type = payload.get("type")
                    event_data = payload.get("data")

                    # ALSO emit chat messages for chat UI
                    await push_chat_message_stream(user_id, event_type, event_data, subnode)
                    full_response += event_data

        ctx["prefetched"][subnode] = full_response
        await push_chat_message_stream(user_id, "done", full_response)
    except Exception as e:
        print(f"[PREFETCH ERROR - {subnode}] {e}")

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
        answer = strip_think(answer)

        ctx["prefetched"][subnode] = answer


        # Store prefetch result
        ctx["prefetched"][subnode] = answer

        # Auto-push if user is viewing this subnode
        if ctx["selected_subnode"] == subnode:
            await push_chat_message(user_id, answer)

    except Exception as e:
        print(f"[PREFETCH ERROR - {subnode}] {e}")

    finally:
        # Clean up pending entry
        ctx["pending"].pop(subnode, subnode)


# =====================================================
# Graph Node Selection Endpoint
# =====================================================
@graph_router.post("/nodes/{node_id}/context")
async def get_node_context(
    node_id: int,
    request: Request,
    user=Depends(get_current_user),
):
    user_id = user["sub"]
    ctx = user_graph_contexts[user_id]
    kg_data = request.app.state.kg_data

    question = ctx.get("latest_question")
    # --------------------------------------------------
    # ROOT NODE
    # --------------------------------------------------
    if node_id == 1:
        ctx["selected_subnode"] = "root"

        if not question:
            await push_chat_message(
                user_id,
                "You've clicked the summary node. Do you want a main summary of the three subjects: Strategic overview, Best practices and Target groups."
                "To proceed. Ask me your question?" 
            )
        else:
            await push_chat_message(
                user_id,
                "You're back on the main summary. "
                f"Would you like to ask a different question than: '{question}'? "
                "**Respond with another question** or type **no** to reuse it."
            )
        # If a prompt was already pending, cancel it and re-ask
        ctx["dialogue_state_asked"] = False
        await push_chat_message_stream(user_id, "done", "", "root")

        ctx["dialogue_state_asked"] = True
        ctx["previous_question"] = question
        return

    # --------------------------------------------------
    # SUBNODE
    # --------------------------------------------------
    if node_id in SUBNODE_MAP:
        subnode = SUBNODE_MAP[node_id]
        ctx["selected_subnode"] = subnode
        # If a prompt was already pending, cancel it and re-ask
        ctx["dialogue_state_asked"] = False
        if not question:
            await push_chat_message(
                user_id,
                "You've selected subset "
                f"{subnode}. What question do you want to ask?" 
            )
        else:
            await push_chat_message(
                user_id,
                "You've selected subset "
                f"{subnode}. Would you like to ask a different question than: "
                f"'{question}'? **Respond with another question** or type **no** "
                "to reuse it."
            )

        await push_chat_message_stream(user_id, "done", "", subnode)

        ctx["dialogue_state_asked"] = True
        ctx["previous_question"] = question
        return

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

    edges = [
        rel for rel in kg_data.relations.values()
        if int(rel.sourceId) == node_id or int(rel.targetId) == node_id
    ]

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
