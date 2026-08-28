from fastapi import Depends, APIRouter, Request
from src.endpoints.auth import get_current_user


asset_router = APIRouter()


@asset_router.get("/")
async def root(request: Request, user=Depends(get_current_user)):
    kg_data = request.app.state.kg_data
    if kg_data is None:
        return {
            "status": "error",
            "message": "Knowledge graph data not loaded",
            "version": "0.1.0",
        }

    return {
        "status": "ok",
        "user": user,
        "version": "0.1.0",
        "data": {
            "entities_count": len(kg_data.entities),
            "relations_count": len(kg_data.relations),
            "questions_count": len(kg_data.questions),
        },
    }
