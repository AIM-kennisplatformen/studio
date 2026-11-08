from typing import TypedDict


class AgentEvent(TypedDict):
    """Event yielded by stream_agent_events."""

    type: str
    data: str
    timestamp: float
