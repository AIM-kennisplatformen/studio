import asyncio
import hashlib

import pytest

from backend.stores.pdf_store import PdfStore


def _sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def test_is_valid_sha256_accepts_well_formed_digests_and_rejects_others():
    assert PdfStore.is_valid_sha256("a" * 64)
    assert PdfStore.is_valid_sha256(_sha256(b"hello"))
    assert not PdfStore.is_valid_sha256("A" * 64)  # uppercase not accepted
    assert not PdfStore.is_valid_sha256("a" * 63)
    assert not PdfStore.is_valid_sha256("not-a-hash")
    assert not PdfStore.is_valid_sha256("")


def test_save_then_read_round_trips_content(tmp_path):
    async def exercise():
        store = PdfStore()
        await store.connect({"pdf_storage_dir": str(tmp_path)})

        content = b"%PDF-1.4 fake pdf bytes"
        digest = _sha256(content)

        store.save(digest, content)

        assert store.exists(digest)
        assert store.read(digest) == content

    asyncio.run(exercise())


def test_save_rejects_content_that_does_not_match_the_given_hash(tmp_path):
    async def exercise():
        store = PdfStore()
        await store.connect({"pdf_storage_dir": str(tmp_path)})

        wrong_digest = _sha256(b"something else entirely")

        with pytest.raises(ValueError):
            store.save(wrong_digest, b"actual content")

        assert not store.exists(wrong_digest)

    asyncio.run(exercise())


def test_save_is_a_no_op_when_the_same_content_is_already_stored(tmp_path):
    async def exercise():
        store = PdfStore()
        await store.connect({"pdf_storage_dir": str(tmp_path)})

        content = b"repeat upload of the same paper"
        digest = _sha256(content)

        store.save(digest, content)
        path = store._path(digest)
        first_mtime = path.stat().st_mtime_ns

        store.save(digest, content)

        assert path.stat().st_mtime_ns == first_mtime

    asyncio.run(exercise())


def test_read_returns_none_for_a_missing_pdf(tmp_path):
    async def exercise():
        store = PdfStore()
        await store.connect({"pdf_storage_dir": str(tmp_path)})

        assert store.read("a" * 64) is None

    asyncio.run(exercise())


def test_delete_reports_whether_a_file_was_actually_removed(tmp_path):
    async def exercise():
        store = PdfStore()
        await store.connect({"pdf_storage_dir": str(tmp_path)})

        content = b"a paper to delete"
        digest = _sha256(content)
        store.save(digest, content)

        assert store.delete(digest) is True
        assert store.read(digest) is None
        assert store.delete(digest) is False

    asyncio.run(exercise())


def test_methods_raise_before_connect_is_called():
    store = PdfStore()

    with pytest.raises(RuntimeError):
        store.exists("a" * 64)


def test_connect_is_idempotent(tmp_path):
    async def exercise():
        store = PdfStore()
        await store.connect({"pdf_storage_dir": str(tmp_path)})
        await store.connect({"pdf_storage_dir": str(tmp_path / "ignored")})

        assert store.directory == tmp_path

    asyncio.run(exercise())
