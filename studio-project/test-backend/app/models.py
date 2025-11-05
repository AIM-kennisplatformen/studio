from pydantic import BaseModel
from typing import List, Optional


class Node(BaseModel):
    """Graph node representation"""
    id: str
    type: str = "unknown"
    label: str
    attributes: dict  # Additional attributes for the node


class Edge(BaseModel):
    """Graph edge representation"""
    id: str
    sourceId: str
    targetId: str
    labelToSource: Optional[str] = None
    labelToTarget: Optional[str] = None
    type: str = "unknown"
    attributes: Optional[dict]  # Additional attributes for the edge


class Source(BaseModel):
    """Source citation or reference"""
    title: str
    type: str   # file type for icon, e.g., 'pdf', 'docx', 'url'
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