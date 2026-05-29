import os
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request as UrlRequest
from urllib.request import urlopen

from fastapi import HTTPException, Depends, APIRouter, Request
from fastapi.responses import RedirectResponse, FileResponse, Response, HTMLResponse

from backend.config import config
from backend.endpoints.auth import get_current_user


asset_router = APIRouter()
FRONTEND_HMR_MARKER = os.getenv("FRONTEND_HMR_MARKER", "/tmp/studio_frontend_hmr")


def vite_dev_server_url():
    if os.path.exists(FRONTEND_HMR_MARKER):
        return config["vite_dev_server_url"].rstrip("/")
    return None


def vite_proxy_response(request: Request, path: str = ""):
    dev_server_url = vite_dev_server_url()
    if not dev_server_url:
        return None

    path = path.strip("/")
    quoted_path = quote(path, safe="/@.-_~")
    target = f"{dev_server_url}/app/{quoted_path}" if path else f"{dev_server_url}/app/"
    if request.url.query:
        target = f"{target}?{request.url.query}"

    try:
        upstream_request = UrlRequest(target, headers={"Accept": request.headers.get("accept", "*/*")})
        with urlopen(upstream_request, timeout=10) as upstream:
            headers = {
                key: value
                for key, value in upstream.headers.items()
                if key.lower() in {"content-type", "cache-control", "etag"}
            }
            return Response(upstream.read(), status_code=upstream.status, headers=headers)
    except HTTPError as exc:
        headers = {
            key: value
            for key, value in exc.headers.items()
            if key.lower() in {"content-type", "cache-control", "etag"}
        }
        return Response(exc.read(), status_code=exc.status or 500, headers=headers)
    except URLError as exc:
        raise HTTPException(502, f"Vite dev server unavailable: {exc}") from exc


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
async def serve_frontend(request: Request, path: str, user=Depends(get_current_user)):
    if response := vite_proxy_response(request, path):
        return response

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
async def app_root(request: Request, user=Depends(get_current_user)):
    if response := vite_proxy_response(request):
        return response

    return RedirectResponse("/app/")


@frontend.get("/pdfjs/web/viewer.html")
async def serve_pdf_viewer(file: str = "", user=Depends(get_current_user)):
    viewer_path = os.path.join(detect_frontend_dir(), "pdfjs", "web", "viewer.html")
    content = open(viewer_path).read()
    # Inject custom CSS before </head>
    custom_css = "<style>#downloadButton, #printButton, #secondaryPrint { display: none !important; }</style>"
    content = content.replace("</head>", f"{custom_css}</head>")
    return HTMLResponse(content=content)


@frontend.get("/pdfjs/{path:path}")
async def serve_pdfjs(path: str, user=Depends(get_current_user)):
    d = detect_frontend_dir()
    if not d:
        raise HTTPException(500, "Frontend build not found")
    requested = os.path.join(d, "pdfjs", path)
    if not os.path.exists(requested):
        raise HTTPException(404)
    return FileResponse(requested)

@frontend.get("/assets/{path:path}")
async def serve_assets(path: str, user=Depends(get_current_user)):
    d = detect_frontend_dir()
    if not d:
        raise HTTPException(500, "Frontend build not found")

    requested = os.path.join(d, "assets", path)
    if not os.path.exists(requested):
        raise HTTPException(404)

    return FileResponse(requested)
