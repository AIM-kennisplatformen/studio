import asyncio
import hashlib
from io import BytesIO

import pytest
from fastapi import HTTPException, UploadFile

from backend.endpoints import pdfs as pdfs_module
from backend.stores.pdf_store import PdfStore


def _sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _upload_file(content: bytes, content_type: str = "application/pdf") -> UploadFile:
    return UploadFile(filename="paper.pdf", file=BytesIO(content), headers={"content-type": content_type})


def _install_store(monkeypatch, tmp_path) -> PdfStore:
    store = PdfStore()
    asyncio.run(store.connect({"pdf_storage_dir": str(tmp_path)}))
    monkeypatch.setattr(pdfs_module, "pdf_store", store)
    return store


def test_upload_pdf_stores_content_and_returns_its_size(monkeypatch, tmp_path):
    store = _install_store(monkeypatch, tmp_path)
    content = b"%PDF-1.4 a real-ish paper"
    digest = _sha256(content)

    response = asyncio.run(
        pdfs_module.upload_pdf(digest, _upload_file(content), app="scepa-rs")
    )

    assert response == {"sha256": digest, "size": len(content)}
    assert store.read(digest) == content


def test_upload_pdf_rejects_a_malformed_sha256_path_param(monkeypatch, tmp_path):
    _install_store(monkeypatch, tmp_path)

    with pytest.raises(HTTPException) as exc:
        asyncio.run(
            pdfs_module.upload_pdf("not-a-hash", _upload_file(b"content"), app="scepa-rs")
        )
    assert exc.value.status_code == 400


def test_upload_pdf_rejects_content_that_does_not_match_the_hash(monkeypatch, tmp_path):
    _install_store(monkeypatch, tmp_path)
    digest = _sha256(b"expected content")

    with pytest.raises(HTTPException) as exc:
        asyncio.run(
            pdfs_module.upload_pdf(digest, _upload_file(b"different content"), app="scepa-rs")
        )
    assert exc.value.status_code == 400


def test_upload_pdf_rejects_a_non_pdf_content_type(monkeypatch, tmp_path):
    _install_store(monkeypatch, tmp_path)
    content = b"just text"
    digest = _sha256(content)

    with pytest.raises(HTTPException) as exc:
        asyncio.run(
            pdfs_module.upload_pdf(digest, _upload_file(content, "text/plain"), app="scepa-rs")
        )
    assert exc.value.status_code == 415


def test_get_pdf_returns_stored_bytes(monkeypatch, tmp_path):
    store = _install_store(monkeypatch, tmp_path)
    content = b"%PDF-1.4 stored paper"
    digest = _sha256(content)
    store.save(digest, content)

    response = asyncio.run(pdfs_module.get_pdf(digest, caller="scepa-rs"))

    assert response.body == content
    assert response.media_type == "application/pdf"


def test_get_pdf_returns_404_when_missing(monkeypatch, tmp_path):
    _install_store(monkeypatch, tmp_path)

    with pytest.raises(HTTPException) as exc:
        asyncio.run(pdfs_module.get_pdf("a" * 64, caller="scepa-rs"))
    assert exc.value.status_code == 404


def test_delete_pdf_removes_an_existing_file(monkeypatch, tmp_path):
    store = _install_store(monkeypatch, tmp_path)
    content = b"%PDF-1.4 to be deleted"
    digest = _sha256(content)
    store.save(digest, content)

    asyncio.run(pdfs_module.delete_pdf(digest, app="scepa-rs"))

    assert store.read(digest) is None


def test_delete_pdf_returns_404_when_missing(monkeypatch, tmp_path):
    _install_store(monkeypatch, tmp_path)

    with pytest.raises(HTTPException) as exc:
        asyncio.run(pdfs_module.delete_pdf("a" * 64, app="scepa-rs"))
    assert exc.value.status_code == 404
