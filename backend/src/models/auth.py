"""Authentication-related data shapes."""

from typing import TypedDict


class AuthentikUser(TypedDict):
    """Shape of the Authentik userinfo dict saved in the session by /auth/callback."""

    sub: str


class AuthentikToken(TypedDict):
    """Token response returned by Authentik, including userinfo claims."""

    userinfo: AuthentikUser


class MeResponse(TypedDict):
    """Response returned by the /me endpoint."""

    authenticated: bool
    user: AuthentikUser
