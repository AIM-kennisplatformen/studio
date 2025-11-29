"""Data loader for knowledge graph example data and QnA questions."""

import json
from typing import Dict, List, Any
from .models import Node, Edge


class KnowledgeGraphData:
    """Container for loaded knowledge graph data."""
    
    def __init__(self):
        self.entities: Dict[int, Node] = {}
        self.relations: Dict[int, Edge] = {}
        self.questions: List[Dict[str, Any]] = []
    
    def load_from_files(self, data_path: str, questions_path: str):
        """Load data from JSON files."""
        # Load example data
        with open(data_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Convert nuggets to Node models
        for nugget in data.get('nuggets', []):
            entity_id = nugget['id']
            
            # Build attributes dict from all fields except id, type, and title
            attributes = {k: v for k, v in nugget.items() 
                         if k not in ['id', 'type', 'title']}
            
            # Create Node
            node = Node(
                id=str(entity_id),
                type=nugget.get('type', 'nugget'),
                label=nugget.get('title', f"Entity {entity_id}"),
                attributes=attributes
            )
            
            self.entities[entity_id] = node
        
        # Convert relationships to Edge models
        for relationship in data.get('relationships', []):
            rel_id = relationship['id']
            
            # Build attributes dict from description if present
            attributes = {}
            if 'description' in relationship:
                attributes['description'] = relationship['description']
            
            # Create Edge
            edge = Edge(
                id=str(rel_id),
                sourceId=str(relationship['source_id']),
                targetId=str(relationship['target_id']),
                labelToTarget=relationship.get('label_forward'),
                labelToSource=relationship.get('label_backward'),
                type='relation',
                attributes=attributes
            )
            
            self.relations[rel_id] = edge
        
        # Load QnA questions
        with open(questions_path, 'r', encoding='utf-8') as f:
            self.questions = json.load(f)
    
    def get_entity(self, entity_id: int) -> Node | None:
        """Get entity by ID."""
        return self.entities.get(entity_id)
    
    def get_relation(self, relation_id: int) -> Edge | None:
        """Get relation by ID."""
        return self.relations.get(relation_id)
    
    def get_question(self, question_id: int) -> Dict[str, Any] | None:
        """Get question by ID."""
        for q in self.questions:
            if q.get('id') == question_id:
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

    return kg_data