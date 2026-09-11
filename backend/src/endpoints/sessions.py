from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status

from src.endpoints.auth import get_current_user
from src.models.session import Session, SessionDetail, UpdateSessionRequest
from src.stores.postgres import postgres_store
from src.utility.session_store import (
    ACTIVE_SESSION_KEY,
    set_active_session_id,
)


sessions_router = APIRouter(tags=["sessions"])


@sessions_router.get("/sessions", response_model=list[Session])
async def list_sessions(user=Depends(get_current_user)):
    user_id = user["sub"]
    return await postgres_store.list_sessions(user_id)


@sessions_router.post("/sessions", response_model=Session)
async def create_session(request: Request, user=Depends(get_current_user)):
    user_id = user["sub"]
    title_type = request.session.get("title_type", "adaptive")
    session = await postgres_store.create_session(user_id, title_type=title_type)
    request.session[ACTIVE_SESSION_KEY] = str(session.session_id)
    set_active_session_id(user_id, session.session_id)
    return session


@sessions_router.get("/sessions/{session_id}", response_model=SessionDetail)
async def get_session(session_id: UUID, user=Depends(get_current_user)):
    user_id = user["sub"]
    session = await postgres_store.get_session(user_id, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    messages = await postgres_store.list_messages(user_id, session_id)
    return SessionDetail(session=session, messages=messages)


@sessions_router.patch("/sessions/{session_id}", response_model=Session)
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


@sessions_router.post("/sessions/{session_id}", response_model=Session)
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


@sessions_router.delete(
    "/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def delete_session(
    session_id: UUID,
    user=Depends(get_current_user),
):
    user_id = user["sub"]
    session = await postgres_store.get_session(user_id, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    await postgres_store.delete_session(user_id, session_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
