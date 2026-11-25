from fastapi import APIRouter, Depends, HTTPException
from loguru import logger
from pydantic import BaseModel, Field

from src.endpoints.auth import get_current_user
from src.tours.selector import select_tour
from src.utility.decider import Decider

tours_router: APIRouter = APIRouter()

_decider: Decider | None = None


def get_decider() -> Decider:
    """Lazily build the Nebius-backed decider; 503 when no key is configured."""
    global _decider
    if _decider is None:
        try:
            _decider = Decider.from_env()
        except RuntimeError as exc:
            logger.warning(f"Tour selection unavailable: {exc}")
            raise HTTPException(
                status_code=503, detail="Tour selection is not configured"
            ) from exc
    return _decider


class TourSelectRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)


class TourSelectResponse(BaseModel):
    tour_id: str | None
    probability: float
    distribution: dict[str, float]
    coverage: float


@tours_router.post("/tours/select", response_model=TourSelectResponse)
async def select_tour_endpoint(
    body: TourSelectRequest,
    user=Depends(get_current_user),
    decider: Decider = Depends(get_decider),
) -> TourSelectResponse:
    try:
        selection = await select_tour(decider, body.question)
    except Exception as exc:
        logger.exception("Tour selection failed")
        raise HTTPException(status_code=502, detail="Tour selection failed") from exc
    return TourSelectResponse(**selection.as_dict())
