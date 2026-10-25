from typing import Annotated, cast

from authlib.integrations.starlette_client import OAuth
from fastapi import APIRouter, Depends, HTTPException, Request, WebSocket
from fastapi.responses import RedirectResponse

from src.config import config
from src.models.auth import AuthentikUser, MeResponse
from src.utility.authentik import AuthentikOAuthApp

# -------------------------------------------------------
# OAuth Client Setup
# -------------------------------------------------------

oauth = OAuth()
# authlib does not publish type hints for OAuth.register.
oauth.register(  # pyright: ignore[reportUnknownMemberType]
    name="authentik",
    server_metadata_url=config["discovery_url"],
    client_id=config["client_id"],
    client_secret=config["client_secret"],
    client_kwargs={"scope": "openid email profile"},
)

auth_router = APIRouter()


authentik = cast(AuthentikOAuthApp, oauth.authentik)


# -------------------------------------------------------
# Helpers
# -------------------------------------------------------


def get_current_user(request: Request) -> AuthentikUser:
    """
    Load the authenticated user from the session for HTTP requests.
    Redirects to login if missing.
    """
    user = request.session.get("user")
    if not user:
        raise HTTPException(
            status_code=307,
            headers={"Location": f"{config['base_url']}/auth/login"},
        )
    return cast(AuthentikUser, user)


CurrentUser = Annotated[AuthentikUser, Depends(get_current_user)]


# -------------------------------------------------------
# HTTP Authentication Flow
# -------------------------------------------------------


@auth_router.get("/auth/login")
async def login(request: Request) -> RedirectResponse:
    """
    Redirect the user to Authentik for authentication.
    """
    return await authentik.authorize_redirect(request, config["oauth_redirect_uri"])


@auth_router.get("/auth/callback")
async def callback(request: Request) -> RedirectResponse:
    """
    OAuth callback endpoint: retrieves tokens and stores userinfo in session.
    """
    token = await authentik.authorize_access_token(request)
    request.session["user"] = dict(token["userinfo"])
    return RedirectResponse(f"{config['frontend_base_url']}/")


@auth_router.get("/auth/logout")
async def logout(request: Request) -> RedirectResponse:
    """
    Clear the user's session and log them out.
    """
    request.session.clear()
    return RedirectResponse(config["logout_url"])


@auth_router.get("/me", response_model=None)
async def me(request: Request) -> MeResponse:
    """
    Return authenticated user metadata.
    """
    user = request.session.get("user")
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return {"authenticated": True, "user": cast(AuthentikUser, user)}


# -------------------------------------------------------
# WebSocket Authentication
# -------------------------------------------------------


async def get_current_user_ws(websocket: WebSocket) -> AuthentikUser | None:
    """
    Load the authenticated user for WebSocket connections.
    Reads from SessionMiddleware's scope["session"], same as HTTP.
    """
    session = cast(dict[str, object], websocket.scope.get("session") or {})
    user = session.get("user")

    if not user:
        await websocket.close(code=4401)
        return None

    return cast(AuthentikUser, user)
