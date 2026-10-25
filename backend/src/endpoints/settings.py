from fastapi import APIRouter, Request
from pydantic import BaseModel

from src.endpoints.auth import CurrentUser
from src.endpoints.chat import user_title_settings

settings_router: APIRouter = APIRouter()


class UpdateSettingsRequest(BaseModel):
    dynamic_title: bool


@settings_router.get("/settings")
async def get_settings(user: CurrentUser) -> dict[str, bool]:
    user_id: str = user["sub"]
    return {
        "dynamic_title": user_title_settings.get(user_id, True),
    }


@settings_router.put("/settings")
async def update_settings(
    body: UpdateSettingsRequest,
    request: Request,
    user: CurrentUser,
) -> dict[str, bool]:
    user_id: str = user["sub"]
    request.session["dynamic_title"] = body.dynamic_title
    user_title_settings[user_id] = body.dynamic_title
    return {"dynamic_title": body.dynamic_title}
