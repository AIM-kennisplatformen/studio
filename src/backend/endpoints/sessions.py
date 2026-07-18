from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request

from backend.endpoints.auth import get_current_user
from backend.models.session import Session, SessionDetail, UpdateSessionRequest
from backend.stores.postgres import postgres_store
from backend.utility.session_store import (
    ACTIVE_SESSION_KEY,
    set_active_session_id,
)


sessions_router = APIRouter(prefix="/sessions", tags=["sessions"])


@sessions_router.get("/", response_model=list[Session])
async def list_sessions(user=Depends(get_current_user)):
    user_id = user["sub"]
    return await postgres_store.list_sessions(user_id)


@sessions_router.post("/", response_model=Session)
async def create_session(request: Request, user=Depends(get_current_user)):
    user_id = user["sub"]
    title_type = request.session.get("title_type", "adaptive")
    session = await postgres_store.create_session(user_id, title_type=title_type)
    request.session[ACTIVE_SESSION_KEY] = str(session.session_id)
    set_active_session_id(user_id, session.session_id)
    return session


@sessions_router.get("/{session_id}", response_model=SessionDetail)
async def get_session(session_id: UUID, user=Depends(get_current_user)):
    user_id = user["sub"]
    session = await postgres_store.get_session(user_id, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    messages = await postgres_store.list_messages(user_id, session_id)
    return SessionDetail(session=session, messages=messages)


@sessions_router.patch("/{session_id}", response_model=Session)
async def update_session(
    session_id: UUID,
    body: UpdateSessionRequest,
    user=Depends(get_current_user),
):
    user_id = user["sub"]
    session = await postgres_store.get_session(user_id, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    title_overwritten = body.name is not None
    updated = await postgres_store.update_session_meta(
        user_id,
        session_id,
        name=body.name,
        title_type=body.title_type,
        title_overwritten=title_overwritten or None,
    )
    return updated


@sessions_router.post("/{session_id}", response_model=Session)
async def activate_session(
    session_id: UUID,
    request: Request,
    user=Depends(get_current_user),
):
    user_id = user["sub"]
    session = await postgres_store.get_session(user_id, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    request.session[ACTIVE_SESSION_KEY] = str(session.session_id)
    set_active_session_id(user_id, session.session_id)
    return session
