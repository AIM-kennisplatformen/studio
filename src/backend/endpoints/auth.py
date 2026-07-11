import secrets

from fastapi import APIRouter, Request, Depends, HTTPException, WebSocket
from fastapi.responses import RedirectResponse
from authlib.integrations.starlette_client import OAuth

from backend.config import config

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
        raise HTTPException(status_code=307, headers={"Location": "/auth/login"})
    return user


def _parse_api_keys(raw: str) -> dict[str, str]:
    """Parse "app-name:key,other-app:key" into {app_name: key}."""
    keys: dict[str, str] = {}
    for entry in raw.split(","):
        name, _, key = entry.strip().partition(":")
        if name and key:
            keys[name] = key
    return keys


_API_KEYS = _parse_api_keys(config["pdf_api_keys"])


def require_api_key(request: Request) -> str:
    """
    Authenticate a machine client via a static bearer API key.

    Separate from get_current_user, which is for interactive browser
    sessions via OAuth: machine clients (e.g. scepa-rs, upload_interface)
    have no browser session to hold a cookie in. Returns the calling
    application's configured name on success (for logging/auditing).
    """
    scheme, _, presented = request.headers.get("authorization", "").partition(" ")
    if scheme.lower() != "bearer" or not presented:
        raise HTTPException(status_code=401, detail="Missing or malformed Authorization header")

    for app_name, key in _API_KEYS.items():
        if secrets.compare_digest(presented, key):
            return app_name

    raise HTTPException(status_code=401, detail="Invalid API key")


def get_current_user_or_api_key(request: Request) -> str:
    """
    Authenticate a PDF read via either an authenticated browser session or a
    machine client's API key.

    The frontend's PDF viewer fetches PDFs directly by URL with credentials
    (pdf.js's `getDocument({ url, withCredentials: true })`), i.e. a browser
    session cookie, not a bearer token — so read access needs to accept both,
    unlike the write endpoints, which are machine-only and stay on
    require_api_key. Returns a string identifying the caller (the session
    user's id, or the API key's app name) for logging/auditing.
    """
    user = request.session.get("user")
    if user:
        return str(user.get("sub") or user.get("email") or "session-user")

    scheme, _, presented = request.headers.get("authorization", "").partition(" ")
    if scheme.lower() == "bearer" and presented:
        for app_name, key in _API_KEYS.items():
            if secrets.compare_digest(presented, key):
                return app_name

    raise HTTPException(status_code=401, detail="Authentication required")


# -------------------------------------------------------
# HTTP Authentication Flow
# -------------------------------------------------------

@auth_router.get("/auth/login")
async def login(request: Request):
    """
    Redirect the user to Authentik for authentication.
    """
    redirect_uri = config["base_url"] + "/auth/callback"
    return await oauth.authentik.authorize_redirect(request, redirect_uri)


@auth_router.get("/auth/callback")
async def callback(request: Request):
    """
    OAuth callback endpoint: retrieves tokens and stores userinfo in session.
    """
    token = await oauth.authentik.authorize_access_token(request)
    request.session["user"] = dict(token["userinfo"])
    return RedirectResponse("/app")


@auth_router.get("/auth/logout")
async def logout(request: Request):
    """
    Clear the user's session and log them out.
    """
    request.session.clear()
    return RedirectResponse(config["logout_url"])


@auth_router.get("/me")
async def me(user=Depends(get_current_user)):
    """
    Return authenticated user metadata.
    """
    return {"authenticated": True, "user": user}

@auth_router.get("/")
async def redirect_to_app(request: Request):
       return RedirectResponse("/app")

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
