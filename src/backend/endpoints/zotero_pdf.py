"""
pdf_proxy.py
~~~~~~~~~~~~
FastAPI router that proxies PDF files from Zotero.

Mount in your studio app:
    from .pdf_proxy import router as pdf_router
    app.include_router(pdf_router, prefix="/api")

Environment variables required:
    ZOTERO_API_KEY       — Zotero API key
    ZOTERO_LIBRARY_ID    — Zotero group library ID
    ZOTERO_LIBRARY_TYPE  — 'groups' or 'users' (default: groups)
"""

from __future__ import annotations

import os
import httpx

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from backend.endpoints.auth import get_current_user

router = APIRouter()


def _zotero_url(item_key: str) -> str:
    library_type = os.getenv("ZOTERO_LIBRARY_TYPE", "groups")
    library_id   = os.environ["ZOTERO_LIBRARY_ID"]
    return f"https://api.zotero.org/{library_type}/{library_id}/items/{item_key}/file"


def _zotero_headers() -> dict[str, str]:
    return {"Zotero-API-Key": os.environ["ZOTERO_API_KEY"]}


@router.get(
    "/pdf/zotero/{item_key}",
    summary="Stream a PDF from Zotero by item key",
)
async def proxy_zotero_pdf(item_key: str,  user=Depends(get_current_user)) -> StreamingResponse:
    async with httpx.AsyncClient(follow_redirects=True, timeout=30) as client:
        # Step 1: get the attachment key from the parent item
        meta_url = f"https://api.zotero.org/{os.getenv('ZOTERO_LIBRARY_TYPE', 'groups')}/{os.environ['ZOTERO_LIBRARY_ID']}/items/{item_key}"
        meta = await client.get(meta_url, headers=_zotero_headers())
        meta.raise_for_status()
        
        attachment_href = meta.json().get("links", {}).get("attachment", {}).get("href", "")
        if not attachment_href:
            raise HTTPException(status_code=404, detail=f"No attachment found for {item_key}")
        attachment_key = attachment_href.rstrip("/").split("/")[-1]

        # Step 2: fetch the actual file
        r = await client.get(_zotero_url(attachment_key), headers=_zotero_headers())
        r.raise_for_status()
        content = r.content

    return StreamingResponse(
        content=iter([content]),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'inline; filename="{item_key}.pdf"',
            "Content-Length":      str(len(content)),
            "Cache-Control":       "private, max-age=3600",
        },
    )