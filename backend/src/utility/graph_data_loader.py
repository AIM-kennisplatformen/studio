"""Data loader for the FCose graph payload and QnA questions.

The payload file uses the same ``nodes``/``edges`` contract that
``GET /api/graph`` returns, so the mock export and the future TypeDB MCP path
share one structure.
"""

import json
from pathlib import Path
from typing import Dict, List, Any

from src.utility.graph_api_models import Edge, GraphResponse, Node


class KnowledgeGraphData:
    """Container for loaded knowledge graph data."""

    def __init__(self) -> None:
        self.entities: Dict[int, Node] = {}
        self.relations: Dict[int, Edge] = {}
        self.questions: List[Dict[str, Any]] = []

    def load_from_files(self, data_path: str) -> None:
        """Load a graph payload from JSON."""
        with open(data_path, "r", encoding="utf-8") as f:
            payload = GraphResponse.model_validate(json.load(f))

        for node in payload.nodes:
            self.entities[node.id] = node

        for edge in payload.edges:
            self.relations[edge.id] = edge

    def get_entity(self, entity_id: int) -> Node | None:
        """Get entity by ID."""
        return self.entities.get(entity_id)

    def get_relation(self, relation_id: int) -> Edge | None:
        """Get relation by ID."""
        return self.relations.get(relation_id)

    def get_question(self, question_id: int) -> Dict[str, Any] | None:
        """Get question by ID."""
        for q in self.questions:
            if q.get("id") == question_id:
                return q
        return None

    def get_all_entities(self) -> List[Node]:
        """Get all entities as a list."""
        return list(self.entities.values())

    def get_all_relations(self) -> List[Edge]:
        """Get all relations as a list."""
        return list(self.relations.values())


def load_knowledge_graph() -> KnowledgeGraphData:
    """Load knowledge graph data from JSON files."""
    kg_data = KnowledgeGraphData()
    # Get paths relative to this file
    base_path = Path(__file__).parent.parent
    data_path = base_path / "knowledge-graph" / "example-data.json"

    kg_data.load_from_files(str(data_path))
    return kg_data
