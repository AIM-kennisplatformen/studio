from typing import cast

from fastapi import APIRouter, FastAPI, Request

from src.endpoints.auth import CurrentUser
from src.models.assets import AssetsError, AssetsSuccess
from src.utility.graph_data_loader import KnowledgeGraphData


asset_router: APIRouter = APIRouter()


@asset_router.get("/", response_model=None)
async def root(
    request: Request,
    user: CurrentUser,
) -> AssetsSuccess | AssetsError:
    app = cast(FastAPI, request.app)
    kg_data = cast(KnowledgeGraphData | None, app.state.kg_data)
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
