from backend.utility.graph_data_loader import load_knowledge_graph
from backend.endpoints.assets import detect_frontend_dir
from fastapi import APIRouter

router = APIRouter()

@router.on_event("startup")
async def startup_event():
    global kg_data
    kg_data = load_knowledge_graph()
    print(f"✓ Loaded {len(kg_data.entities)} entities")
    print(f"✓ Loaded {len(kg_data.relations)} relations")
    print(f"✓ Loaded {len(kg_data.questions)} questions")
    print(f"✓ Frontend directory detected: {detect_frontend_dir()}")
