from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel


class Session(BaseModel):
    session_id: UUID
    user_id: str
    name: str
    updated_at: datetime


class SessionMessage(BaseModel):
    message_id: UUID
    role: Literal["ai", "user"]
    content: str
    created_at: datetime
    updated_at: datetime


class SessionDetail(BaseModel):
    session: Session
    messages: list[SessionMessage]
