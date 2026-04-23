from typing import DefaultDict, Dict, Any
from collections import defaultdict

from fastapi import APIRouter, Depends, Request

from backend.utility.graph_api_models import GraphResponse
from backend.endpoints.auth import get_current_user
from backend.config import subnode_question_prompt

from backend.utility.chat_util import (
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
        await push_chat_message_stream(user_id, "done", full_response, subnode)

    except Exception as e:
        print(f"[PREFETCH ERROR - {subnode}] {e}")


# =====================================================
# Graph Node Selection Endpoint
# =====================================================


#Full graph endpoint, to be called on session start and after each question is answered

@graph_router.get("/graph")
async def get_full_graph(
        request: Request,
        user=Depends(get_current_user)):
   
    user_id = user["sub"]
    ctx = user_graph_contexts[user_id]

    kg_data = request.app.state.kg_data

    if kg_data is None:
        return GraphResponse(
            nodes=[],
            edges=[],
            error="not_loaded",
        )
    
    subnode_name = ctx["selected_subnode"]
    if subnode_name == "root":
        selected_subnode = None
    else:
        selected_subnode = next(
        (n for n in kg_data.entities.values() if n.title == subnode_name),
        None,
    )
    
    return GraphResponse(
        nodes=list(kg_data.entities.values()),
        edges=list(kg_data.relations.values()),
        selected_subnode= selected_subnode,
        error=None,
    ) 
