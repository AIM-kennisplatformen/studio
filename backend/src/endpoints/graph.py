from typing import DefaultDict, Dict, Any
from collections import defaultdict

from fastapi import APIRouter, Depends, Request

from src.utility.graph_api_models import GraphResponse
from src.endpoints.auth import get_current_user
from src.config import subnode_question_prompt

from src.utility.chat_util import (
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
    5: "Best practices / Scientific literature",
    6: "Best practices / Grey literature",
    7: "Best practices / Project reports",
    8: "Target groups / Scientific literature",
    9: "Target groups / Grey literature",
    10: "Target groups / Project reports",
    11: "Strategic overview / Scientific literature",
    12: "Strategic overview / Grey literature",
    13: "Strategic overview / Project reports",
}

SUBNODES = list(SUBNODE_MAP.values())

NODE_CLASSIFICATION_FILTERS = {
    2: (["best_practices"], None),
    3: (["target_groups"], None),
    4: (["strategic_overview"], None),
    5: (["best_practices"], ["scientific_literature"]),
    6: (["best_practices"], ["grey_literature"]),
    7: (["best_practices"], ["project_report"]),
    8: (["target_groups"], ["scientific_literature"]),
    9: (["target_groups"], ["grey_literature"]),
    10: (["target_groups"], ["project_report"]),
    11: (["strategic_overview"], ["scientific_literature"]),
    12: (["strategic_overview"], ["grey_literature"]),
    13: (["strategic_overview"], ["project_report"]),
}

# =====================================================
# Per-user Graph Context
# =====================================================


def _default_user_graph_context() -> Dict[str, Any]:
    return {
        "selected_subnode": "root",
        "selected_node_id": 1,
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


async def fetch_subnode_stream(
    user_id: str,
    question: str,
    subnode: str,
    history_text: str = "",
    trace_id: str | None = None,
    session_id: str | None = None,
    selected_node_id: int | None = None,
):
    """
    Stream an LLM response for a subnode question.

    :param user_id: Authenticated user id.
    :param question: The user's question text.
    :param subnode: Which subnode perspective to use.
    :param history_text: Existing conversation context to include in the prompt.
    :param trace_id: Optional Langfuse trace id to keep all
        observations under a single per-turn trace.
    :param session_id: Optional durable chat session id used as Langfuse session_id.
    """
    ctx = user_graph_contexts[user_id]

    try:
        required_user_personas, required_literature_kinds = (
            NODE_CLASSIFICATION_FILTERS.get(selected_node_id, (None, None))
        )
        synthetic_prompt = subnode_question_prompt(
            question,
            subnode,
            history_text,
            required_user_personas=required_user_personas,
            required_literature_kinds=required_literature_kinds,
        )

        full_response = ""

        # ← Direct generator call — no HTTP, no SSE parsing
        async for evt in stream_agent_events(
            synthetic_prompt,
            user_id=user_id,
            trace_id=trace_id,
            session_id=session_id,
        ):
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


# Full graph endpoint, to be called on session start and after each question is answered


@graph_router.get("/graph")
async def get_full_graph(request: Request, user=Depends(get_current_user)):
    user_id = user["sub"]
    ctx = user_graph_contexts[user_id]

    kg_data = request.app.state.kg_data

    if kg_data is None:
        return GraphResponse(
            nodes=[],
            edges=[],
            error="not_loaded",
        )

    selected_node_id = ctx.get("selected_node_id", 1)
    if selected_node_id == 1:
        selected_subnode = None
    else:
        selected_subnode = kg_data.entities.get(selected_node_id)

    return GraphResponse(
        nodes=list(kg_data.entities.values()),
        edges=list(kg_data.relations.values()),
        selected_subnode=selected_subnode,
        error=None,
    )
