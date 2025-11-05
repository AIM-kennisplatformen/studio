from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import random
from .models import Node, Edge, Source, ChatResponse, ContextResponse
from .data_loader import load_knowledge_graph, KnowledgeGraphData

app = FastAPI(
    title="Knowledge Graph API",
    description="API for chat-based knowledge graph generation and node context retrieval",
    version="0.1.0"
)

# Global knowledge graph data storage
kg_data: KnowledgeGraphData | None = None


@app.on_event("startup")
async def startup_event():
    """Load knowledge graph data on server startup."""
    global kg_data
    try:
        kg_data = load_knowledge_graph()
        print(f"✓ Loaded {len(kg_data.entities)} entities")
        print(f"✓ Loaded {len(kg_data.relations)} relations")
        print(f"✓ Loaded {len(kg_data.questions)} questions")
    except Exception as e:
        print(f"✗ Failed to load knowledge graph data: {e}")
        raise

# Add CORS middleware to allow frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatMessage(BaseModel):
    """Request body for chat messages"""
    message: str


@app.post("/chats/{chat_id}/messages", response_model=ChatResponse)
async def send_chat_message(chat_id: str, payload: ChatMessage):
    """
    Send a message to a chat and receive knowledge graph updates
    
    Args:
        chat_id: Unique identifier for the chat session
        payload: Message string from the user (ignored)
        
    Returns:
        ChatResponse with message, nodes, edges, sources, and optional error
    """
    try:
        # Check if knowledge graph data is loaded
        if kg_data is None:
            return ChatResponse(
                message="",
                nodes=[],
                edges=[],
                sources=[],
                error="Knowledge graph data not loaded"
            )
        
        # Select a random question
        if not kg_data.questions:
            return ChatResponse(
                message="",
                nodes=[],
                edges=[],
                sources=[],
                error="No questions available"
            )
        
        question = random.choice(kg_data.questions)
        
        # Get the answer as the response message
        answer = question.get("answer", "")
        
        # Populate nodes from the entities field
        nodes = []
        for entity_id in question.get("entities", []):
            entity = kg_data.get_entity(entity_id)
            if entity:
                nodes.append(entity)
        
        # Populate edges from the relations field
        edges = []
        for relation_id in question.get("relations", []):
            relation = kg_data.get_relation(relation_id)
            if relation:
                edges.append(relation)
        
        # Return response with populated data
        response = ChatResponse(
            message=answer,
            nodes=nodes,
            edges=edges,
            sources=[],  # Empty as specified
            error=None   # Empty as specified
        )
        
        return response
        
    except Exception as e:
        # Return error in response rather than raising exception
        return ChatResponse(
            message="",
            nodes=[],
            edges=[],
            sources=[],
            error=str(e)
        )


@app.get("/nodes/{node_id}/context", response_model=ContextResponse)
async def get_node_context(node_id: str):
    """
    Get context information for a specific node
    
    Args:
        node_id: Unique identifier for the node
        
    Returns:
        ContextResponse with related nodes, edges, sources, and optional error
    """
    return ChatResponse(
        message="",
        nodes=[],
        edges=[],
        sources=[],
        error="Not implemented yet"
    )

@app.get("/")
async def root():
    """Health check endpoint"""
    if kg_data is None:
        return {
            "status": "error",
            "message": "Knowledge graph data not loaded",
            "version": "0.1.0"
        }
    
    return {
        "status": "ok",
        "message": "Knowledge Graph API is running",
        "version": "0.1.0",
        "data": {
            "entities_count": len(kg_data.entities),
            "relations_count": len(kg_data.relations),
            "questions_count": len(kg_data.questions)
        }
    }