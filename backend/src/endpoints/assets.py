from typing import Annotated, TypedDict, cast

from fastapi import APIRouter, Depends, FastAPI, Request

from src.endpoints.auth import AuthentikUser, get_current_user
from src.utility.graph_data_loader import KnowledgeGraphData


class AssetsCounts(TypedDict):
    entities_count: int
    relations_count: int
    questions_count: int


class AssetsSuccess(TypedDict):
    status: str
    user: AuthentikUser
    version: str
    data: AssetsCounts


class AssetsError(TypedDict):
    status: str
    message: str
    version: str


asset_router = APIRouter()


# pyright: reportAny=false
@asset_router.get("/", response_model=None)
async def root(
    request: Request,
    user: Annotated[AuthentikUser, Depends(get_current_user)],
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
