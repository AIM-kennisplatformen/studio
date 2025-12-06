from backend.endpoints.auth import get_current_user

import os
from fastapi import HTTPException, Depends, APIRouter, Request
from fastapi.responses import RedirectResponse, FileResponse


asset_router = APIRouter()

def detect_frontend_dir():
    POSSIBLE_FRONTEND_DIRS = [
        "kg/app",
        "kg/frontend/dist",
        "kg/build",
        "kg",
        "app",
        "frontend/dist",
        "build",
        "dist"
    ]

    # Primary detection: must contain assets/
    for d in POSSIBLE_FRONTEND_DIRS:
        index_path = os.path.join(d, "index.html")
        assets_path = os.path.join(d, "assets")
        if os.path.exists(index_path) and os.path.isdir(assets_path):
            return d

    # Fallback: any folder with index.html
    for d in POSSIBLE_FRONTEND_DIRS:
        if os.path.exists(os.path.join(d, "index.html")):
            return d

    return None


def get_index_html():
    d = detect_frontend_dir()
    if not d:
        raise HTTPException(
            500,
            "Frontend build missing — index.html not found in any expected locations."
        )
    return os.path.join(d, "index.html")


# ------------------------------------------------------
# Root (Protected)
# ------------------------------------------------------
@asset_router.get("/")
async def root(request: Request, user=Depends(get_current_user)):
    kg_data = request.app.state.kg_data
    if kg_data is None:
        return {
            "status": "error",
            "message": "Knowledge graph data not loaded",
            "version": "0.1.0",
        }

    return {
        "status": "ok",
        "user": user,
        "version": "0.1.0",
        "data": {
            "entities_count": len(kg_data.entities),
            "relations_count": len(kg_data.relations),
            "questions_count": len(kg_data.questions),
        },
    }

# ------------------------------------------------------
# Frontend Auto-Detection + Serving
# ------------------------------------------------------
frontend = APIRouter()


@frontend.get("/app/{path:path}")
async def serve_frontend(path: str, user=Depends(get_current_user)):
    d = detect_frontend_dir()
    if not d:
        raise HTTPException(500, "Frontend build not found — no index.html available.")

    # /app/ or /app → index.html
    if path in ["", "/"]:
        return FileResponse(get_index_html())

    requested = os.path.join(d, path)

    # Serve file if it exists
    if os.path.exists(requested) and os.path.isfile(requested):
        return FileResponse(requested)

    # SPA fallback
    return FileResponse(get_index_html())


@frontend.get("/app")
async def app_root():
    return RedirectResponse("/app/")


@frontend.get("/assets/{path:path}")
async def serve_assets(path: str, user=Depends(get_current_user)):
    d = detect_frontend_dir()
    if not d:
        raise HTTPException(500, "Frontend build not found")

    requested = os.path.join(d, "assets", path)
    if not os.path.exists(requested):
        raise HTTPException(404)

    return FileResponse(requested)



