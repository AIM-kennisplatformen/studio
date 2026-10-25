"""Typed interfaces for the authlib Authentik client."""

from typing import Protocol

from fastapi import Request
from fastapi.responses import RedirectResponse

from src.models.auth import AuthentikToken


class AuthentikOAuthApp(Protocol):
    """Typed subset of authlib's untyped Authentik client."""

    async def authorize_redirect(
        self, request: Request, redirect_uri: str | None = None
    ) -> RedirectResponse: ...

    async def authorize_access_token(self, request: Request) -> AuthentikToken: ...
