from pydantic import BaseModel, Field
from typing import List, Optional


class Node(BaseModel):
    """Graph node representation"""

    id: int
    type: str = "unknown"
    title: str
    attributes: dict = Field(default_factory=dict)  # Additional attributes for the node


class Edge(BaseModel):
    """Graph edge representation"""

    id: int
    source_id: int
    target_id: int
    labelToSource: Optional[str] = None
    labelToTarget: Optional[str] = None
    type: str = "unknown"
    attributes: Optional[dict] = Field(default_factory=dict)  # Additional attributes for the edge


class Source(BaseModel):
    """Source citation or reference"""

    title: str
    type: str  # file type for icon, e.g., 'pdf', 'docx', 'url'
    infoUrl: Optional[str] = None
    downloadUrl: Optional[str] = None
    snippet: Optional[str] = None


class ChatResponse(BaseModel):
    """Response for chat endpoints"""

    message: str
    nodes: List[Node] = []
    edges: List[Edge] = []
    sources: List[Source] = []
    error: Optional[str] = None


class ContextResponse(BaseModel):
    """Response for context endpoints"""

    message: Optional[str] = None
    nodes: List[Node] = []
    edges: List[Edge] = []
    sources: List[Source] = []
    error: Optional[str] = None


class GraphResponse(BaseModel):
    # Added selected subnode to return the currently selected subnode in the graph, which can be used by the frontend to maintain context
    """Response for full graph endpoint"""

    nodes: List[Node] = []
    edges: List[Edge] = []
    selected_subnode: Optional[Node] = None
    # Node the server chose as the centre of this subgraph. None means full graph.
    focus_node_id: Optional[int] = None
    # metadata: dict = {}
    error: Optional[str] = None
