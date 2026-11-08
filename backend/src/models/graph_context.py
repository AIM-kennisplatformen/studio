import asyncio
from typing import TypedDict


class UserGraphContext(TypedDict):
    selected_subnode: str
    selected_node_id: int
    latest_question: str | None
    previous_question: str | None
    latest_keywords: list[str]
    prefetched: dict[str, str]
    pending: dict[str, asyncio.Task[None]]
    dialogue_state_asked: bool
