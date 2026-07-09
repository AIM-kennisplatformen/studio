from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from fastapi.responses import Response
from loguru import logger

from backend.config import config
from backend.endpoints.auth import get_current_user_or_api_key, require_api_key
from backend.stores.pdf_store import pdf_store


# Mounted at /api by main.py, and named "pdf" (singular) rather than "pdfs"
# to match the /api/pdf/{source} path the frontend's citation viewer already
# expects (see totally-stupid's src/frontend/src/lib/pdfCitation.js) — so
# that viewer works against this store unmodified once it's ported over.
pdf_router = APIRouter(prefix="/pdf", tags=["pdf"])


def _validated(sha256: str) -> str:
    # Normalized as a safety net -- callers in other languages don't all
    # default hexdigest() output to lowercase the way Python's hashlib does.
    sha256 = sha256.lower()
    if not pdf_store.is_valid_sha256(sha256):
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail="sha256 must be a 64-character lowercase hex digest",
        )
    return sha256


async def _read_limited(file: UploadFile, max_bytes: int) -> bytes:
    """
    Reads file in chunks, rejecting it once the running total exceeds
    max_bytes -- rejects an oversized upload before it's fully buffered
    into memory, rather than after.
    """
    chunks: list[bytes] = []
    total = 0
    while chunk := await file.read(1024 * 1024):
        total += len(chunk)
        if total > max_bytes:
            raise HTTPException(
                status.HTTP_413_CONTENT_TOO_LARGE,
                detail=f"PDF exceeds the {max_bytes} byte limit",
            )
        chunks.append(chunk)
    return b"".join(chunks)


# PUT, not POST: the identifier is derived from the content itself, so
# "store this content at its own content address" is an idempotent put,
# not a server-assigned creation.
@pdf_router.put("/{sha256}", status_code=status.HTTP_201_CREATED)
async def upload_pdf(sha256: str, file: UploadFile, app: str = Depends(require_api_key)):
    """
    Store a PDF under its own sha256 content hash.

    sha256 is verified server-side against the uploaded bytes and rejected
    on mismatch, so a given hash always maps to exactly one PDF. Re-uploading
    the same content under its own hash is a safe no-op. Machine clients
    only — an authorized application (e.g. scepa-rs) pushes PDFs here after
    ingesting them.
    """
    sha256 = _validated(sha256)

    if file.content_type not in ("application/pdf", "application/octet-stream"):
        raise HTTPException(
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Only PDF files are accepted",
        )

    content = await _read_limited(file, config["pdf_max_size_bytes"])

    try:
        await pdf_store.save(sha256, content)
    except ValueError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    logger.info(f"✓ Stored PDF {sha256} ({len(content)} bytes) via {app}")
    return {"sha256": sha256, "size": len(content)}


@pdf_router.get("/{sha256}")
async def get_pdf(sha256: str, caller: str = Depends(get_current_user_or_api_key)):
    """
    Return the raw PDF bytes stored under sha256.

    Readable by both authorized applications (API key) and the frontend's
    PDF viewer (browser session) — unlike upload/delete, which stay
    machine-only. Responses are cached indefinitely: the identifier is the
    content's own hash, so it can never point to different bytes later.
    """
    sha256 = _validated(sha256)

    content = await pdf_store.read(sha256)
    if content is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=f"No PDF stored under {sha256}")

    return Response(
        content=content,
        media_type="application/pdf",
        headers={"Cache-Control": "private, max-age=31536000, immutable"},
    )


@pdf_router.delete("/{sha256}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_pdf(sha256: str, app: str = Depends(require_api_key)):
    """Delete the PDF stored under sha256. Machine clients only."""
    sha256 = _validated(sha256)

    if not await pdf_store.delete(sha256):
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=f"No PDF stored under {sha256}")
