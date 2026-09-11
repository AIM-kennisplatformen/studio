from fastapi import APIRouter, Request, HTTPException, WebSocket
from fastapi.responses import RedirectResponse
from authlib.integrations.starlette_client import OAuth

from src.config import config

# -------------------------------------------------------
# OAuth Client Setup
# -------------------------------------------------------

oauth = OAuth()
oauth.register(
    name="authentik",
    server_metadata_url=config["discovery_url"],
    client_id=config["client_id"],
    client_secret=config["client_secret"],
    client_kwargs={"scope": "openid email profile"},
)

auth_router = APIRouter()


# -------------------------------------------------------
# Helpers
# -------------------------------------------------------

def get_current_user(request: Request):
    """
    Load the authenticated user from the session for HTTP requests.
    Redirects to login if missing.
    """
    user = request.session.get("user")
    if not user:
        raise HTTPException(status_code=307, headers={"Location": "/api/auth/login"})
    return user


# -------------------------------------------------------
# HTTP Authentication Flow
# -------------------------------------------------------

@auth_router.get("/auth/login")
async def login(request: Request):
    """
    Redirect the user to Authentik for authentication.
    """
    return await oauth.authentik.authorize_redirect(
        request, config["oauth_redirect_uri"]
    )


@auth_router.get("/auth/callback")
async def callback(request: Request):
    """
    OAuth callback endpoint: retrieves tokens and stores userinfo in session.
    """
    token = await oauth.authentik.authorize_access_token(request)
    request.session["user"] = dict(token["userinfo"])
    return RedirectResponse("/")


@auth_router.get("/auth/logout")
async def logout(request: Request):
    """
    Clear the user's session and log them out.
    """
    request.session.clear()
    return RedirectResponse(config["logout_url"])


@auth_router.get("/me")
async def me(request: Request):
    """
    Return authenticated user metadata.
    """
    user = request.session.get("user")
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return {"authenticated": True, "user": user}

# -------------------------------------------------------
# WebSocket Authentication
# -------------------------------------------------------

async def get_current_user_ws(websocket: WebSocket):
    """
    Load the authenticated user for WebSocket connections.
    Reads from SessionMiddleware's scope["session"], same as HTTP.
    """
    session = websocket.scope.get("session") or {}
    user = session.get("user")

    if not user:
        await websocket.close(code=4401)
        return None

    return user
