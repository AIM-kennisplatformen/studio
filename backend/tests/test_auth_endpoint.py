import asyncio

import pytest
from fastapi import HTTPException

from src.endpoints.auth import me


class _FakeRequest:
    def __init__(self, user=None):
        self.session = {"user": user} if user else {}


def test_me_returns_the_authenticated_user():
    user = {"sub": "user-1", "email": "user@example.com"}

    response = asyncio.run(me(_FakeRequest(user)))

    assert response == {"authenticated": True, "user": user}


def test_me_returns_401_without_a_session():
    with pytest.raises(HTTPException, match="Not authenticated") as exc_info:
        asyncio.run(me(_FakeRequest()))

    assert exc_info.value.status_code == 401
