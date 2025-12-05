from backend.config import BASE_URL, DISCOVERY_URL, CLIENT_ID, CLIENT_SECRET
from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import RedirectResponse
from authlib.integrations.starlette_client import OAuth

oauth = OAuth()

oauth.register(
    name="authentik",
    server_metadata_url=DISCOVERY_URL,
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    client_kwargs={"scope": "openid email profile"},
)

auth_router = APIRouter()

def get_current_user(request: Request):
    user = request.session.get("user")
    if not user:
        raise HTTPException(status_code=307, headers={"Location": "/auth/login"})
    return user

@auth_router.get("/auth/login")
async def login(request: Request):
    redirect_uri = BASE_URL + "/auth/callback"
    return await oauth.authentik.authorize_redirect(request, redirect_uri)

@auth_router.get("/auth/callback")
async def callback(request: Request):
    token = await oauth.authentik.authorize_access_token(request)
    request.session["user"] = dict(token["userinfo"])
    return RedirectResponse("/app")

@auth_router.get("/auth/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/")

@auth_router.get("/me")
async def me(user=Depends(get_current_user)):
    return {"authenticated": True, "user": user}
