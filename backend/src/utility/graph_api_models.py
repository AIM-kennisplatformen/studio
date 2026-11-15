from pydantic import BaseModel

from src.models.json_value import JsonValue


class Node(BaseModel):
    """Graph node representation"""

    id: int
    type: str = "unknown"
    title: str
    attributes: dict[str, JsonValue]  # Additional attributes for the node


class Edge(BaseModel):
    """Graph edge representation"""

    id: int
    source_id: int
    target_id: int
    labelToSource: str | None
    labelToTarget: str | None
    type: str = "unknown"
    attributes: dict[str, JsonValue] | None  # Additional attributes for the edge


class Source(BaseModel):
    """Source citation or reference"""

    title: str
    type: str  # file type for icon, e.g., 'pdf', 'docx', 'url'
    infoUrl: str | None
    downloadUrl: str | None
    snippet: str | None


class ChatResponse(BaseModel):
    """Response for chat endpoints"""

    message: str
    nodes: list[Node] = []
    edges: list[Edge] = []
    sources: list[Source] = []
    error: str | None


class ContextResponse(BaseModel):
    """Response for context endpoints"""

    message: str | None
    nodes: list[Node] = []
    edges: list[Edge] = []
    sources: list[Source] = []
    error: str | None


class GraphResponse(BaseModel):
    # Added selected subnode to return the currently selected subnode in the graph, which can be used by the frontend to maintain context
    """Response for full graph endpoint"""

    nodes: list[Node] = []
    edges: list[Edge] = []
    selected_subnode: Node | None = None
    error: str | None
