from html import entities
from queue import Full
from typing import DefaultDict, Dict, Any
from collections import defaultdict

from fastapi import APIRouter, Depends, Request

from backend.utility.graph_api_models import ContextResponse, GraphResponse
from backend.endpoints.auth import get_current_user
from backend.config import subnode_question_prompt

from backend.utility.chat_util import (
    push_chat_message,
    push_chat_message_stream,
    stream_agent_events,
)

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
        "previous_question": None,
        "latest_keywords": [],
        "prefetched": {},  # subnode_name → llm_answer
        "pending": {},  # subnode_name → asyncio.Task
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
        keyword = (
            subnode
            if subnode != "root"
            else "Best practices || Target groups || Strategic overview"
        )

        synthetic_prompt = subnode_question_prompt(question, keyword)

        full_response = ""

        # ← Direct generator call — no HTTP, no SSE parsing
        async for evt in stream_agent_events(synthetic_prompt, user_id=user_id):
            event_type = evt["type"]
            event_data = evt["data"]

            await push_chat_message_stream(user_id, event_type, event_data, subnode)

            if event_type == "on_chat_model_stream" and event_data:
                full_response += event_data

        ctx["prefetched"][subnode] = full_response
        await push_chat_message_stream(user_id, "done", full_response)

    except Exception as e:
        print(f"[PREFETCH ERROR - {subnode}] {e}")


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
                "Do you want to ask an question, answered by the full body of literature? "
                "Please proceed, by asking me your question?",
            )
        else:
            await push_chat_message(
                user_id,
                "Answer a question by using the full body of literature "
                f"Would you like to ask a different question than: '{question}'? "
                "**Respond with another question** or type **yes** to repeat the previous question.",
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
                f"You've selected subset {subnode}. Please ask me your question?",
            )
        else:
            await push_chat_message(
                user_id,
                "You've selected subset "
                f"{subnode}. Please ask me your question using this subset. If you want to repeat your previous question: "
                f"`{question}`"
                " type **yes**, otherwise **Respond with another question**.",
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
        rel
        for rel in kg_data.relations.values()
        if int(rel.sourceId) == node_id or int(rel.targetId) == node_id
    ]

    neighbor_ids = {int(rel.sourceId) for rel in edges} | {
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
        error=None,
    )

#Full graph endpoint, to be called on session start and after each question is answered

@graph_router.get("/graph")
async def get_full_graph(
        request: Request,
        user=Depends(get_current_user)):
   
    user_id = user["sub"]
    # ctx = user_graph_contexts[user_id] # not immediately needed but could be useful for returning user-specific context along with the graph data

    kg_data = request.app.state.kg_data

    if kg_data is None:
        return GraphResponse(
            nodes=[],
            edges=[],
            error="not_loaded",
        )

    return GraphResponse(
        nodes=list(kg_data.entities.values()),
        edges=list(kg_data.relations.values()),
        error=None,
    ) 