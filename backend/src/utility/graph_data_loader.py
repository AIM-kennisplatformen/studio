"""Data loader for knowledge graph example data and QnA questions."""

import json
from collections.abc import Mapping
from pathlib import Path
from typing import cast

from src.models.json_value import JsonValue
from src.utility.graph_api_models import Edge, Node


def _json_object(value: JsonValue, label: str) -> dict[str, JsonValue]:
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be a JSON object")
    return value


def _json_array(value: JsonValue, label: str) -> list[JsonValue]:
    if not isinstance(value, list):
        raise ValueError(f"{label} must be a JSON array")
    return value


def _required_int(obj: Mapping[str, JsonValue], key: str) -> int:
    value = obj.get(key)
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{key} must be an integer")
    return value


def _optional_str(obj: Mapping[str, JsonValue], key: str) -> str | None:
    value = obj.get(key)
    return value if isinstance(value, str) else None


class KnowledgeGraphData:
    """Container for loaded knowledge graph data."""

    def __init__(self) -> None:
        self.entities: dict[int, Node] = {}
        self.relations: dict[int, Edge] = {}
        self.questions: list[dict[str, JsonValue]] = []

    def load_from_files(self, data_path: str) -> None:
        """Load data from JSON files."""
        # Load example data
        with open(data_path, "r", encoding="utf-8") as f:
            data = _json_object(cast(JsonValue, json.load(f)), "graph data")

        # Convert nuggets to Node models
        for nugget_value in _json_array(data.get("nuggets", []), "nuggets"):
            nugget = _json_object(nugget_value, "nugget")
            entity_id = _required_int(nugget, "id")
            attributes = {
                k: v for k, v in nugget.items() if k not in {"id", "type", "title"}
            }
            node = Node(
                id=entity_id,
                type=_optional_str(nugget, "type") or "nugget",
                title=_optional_str(nugget, "title") or f"Entity {entity_id}",
                attributes=attributes,
            )

            self.entities[entity_id] = node

        # Convert relationships to Edge models
        for relationship_value in _json_array(
            data.get("relationships", []), "relationships"
        ):
            relationship = _json_object(relationship_value, "relationship")
            rel_id = _required_int(relationship, "id")

            attributes: dict[str, JsonValue] = {}
            description = _optional_str(relationship, "description")
            if description is not None:
                attributes["description"] = description

            edge = Edge(
                id=rel_id,
                source_id=_required_int(relationship, "source_id"),
                target_id=_required_int(relationship, "target_id"),
                labelToTarget=_optional_str(relationship, "label_forward"),
                labelToSource=_optional_str(relationship, "label_backward"),
                type="relation",
                attributes=attributes,
            )

            self.relations[rel_id] = edge

    def get_entity(self, entity_id: int) -> Node | None:
        """Get entity by ID."""
        return self.entities.get(entity_id)

    def get_relation(self, relation_id: int) -> Edge | None:
        """Get relation by ID."""
        return self.relations.get(relation_id)

    def get_question(self, question_id: int) -> dict[str, JsonValue] | None:
        """Get question by ID."""
        for q in self.questions:
            if q.get("id") == question_id:
                return q
        return None

    def get_all_entities(self) -> list[Node]:
        """Get all entities as a list."""
        return list(self.entities.values())

    def get_all_relations(self) -> list[Edge]:
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
