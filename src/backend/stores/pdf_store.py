import asyncio
import hashlib
import re
from pathlib import Path
from typing import Any

from loguru import logger


SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")


class PdfStore:
    """
    Disk-backed, content-addressed store for PDF files.

    PDFs are stored under a single directory, keyed by the sha256 hex digest
    of their own content — the same SourceHash identifier scepa-rs already
    computes and uses everywhere (TypeDB, Qdrant, JSON export), so a PDF
    stored here correlates directly with its scepa-rs/TypeDB records with no
    separate mapping table.

    Conceptual model
    ----------------
    sha256(bytes) -> PDF file on disk

    Identity
    --------
    Each PDF is identified by its own content hash:
        <storage_dir>/<sha256>.pdf

    Behaviour
    ---------
    - connect() ensures the storage directory exists
    - save() verifies the caller-supplied hash actually matches the content
      before writing, and is a no-op if the file is already present (same
      hash implies same content, so re-uploads are safe)
    - read() returns the raw bytes for a stored PDF, or None if missing
    - delete() removes a stored PDF, returning whether one was actually removed

    All filesystem I/O runs in a worker thread (asyncio.to_thread) rather
    than blocking the event loop directly.
    """

    def __init__(self) -> None:
        self.directory: Path | None = None

    async def connect(self, config_dict: dict[str, Any]) -> None:
        """
        Ensure the configured storage directory exists.

        Parameters
        ----------
        config_dict
            Dictionary containing ``pdf_storage_dir``, the directory PDFs are
            read from and written to.

        The method is idempotent for an already connected store.
        """
        if self.directory is not None:
            return

        directory = Path(config_dict["pdf_storage_dir"])
        await asyncio.to_thread(directory.mkdir, parents=True, exist_ok=True)
        self.directory = directory
        logger.info(f"✓ PDF storage ready at {directory}")

    async def close(self) -> None:
        """Release the store's reference to its storage directory."""
        self.directory = None

    def _ensure_connected(self) -> None:
        if self.directory is None:
            raise RuntimeError(
                f"{self.__class__.__name__} used before connect() was called"
            )

    @staticmethod
    def is_valid_sha256(value: str) -> bool:
        """Return whether value is a well-formed lowercase sha256 hex digest."""
        return bool(SHA256_PATTERN.fullmatch(value))

    def _path(self, sha256: str) -> Path:
        assert self.directory is not None
        return self.directory / f"{sha256}.pdf"

    async def exists(self, sha256: str) -> bool:
        """Return whether a PDF is stored under sha256."""
        self._ensure_connected()
        return await asyncio.to_thread(self._path(sha256).is_file)

    async def save(self, sha256: str, content: bytes) -> None:
        """
        Store content under sha256.

        Raises ValueError if content does not actually hash to sha256.
        Writing is skipped (not an error) if the file is already present.
        """
        self._ensure_connected()

        actual = hashlib.sha256(content).hexdigest()
        if actual != sha256:
            raise ValueError(
                f"content hash {actual} does not match provided identifier {sha256}"
            )

        await asyncio.to_thread(self._write_sync, self._path(sha256), content)

    @staticmethod
    def _write_sync(path: Path, content: bytes) -> None:
        if path.exists():
            return
        _ = path.write_bytes(content)

    async def read(self, sha256: str) -> bytes | None:
        """Return the stored PDF's bytes, or None if nothing is stored under sha256."""
        self._ensure_connected()
        return await asyncio.to_thread(self._read_sync, self._path(sha256))

    @staticmethod
    def _read_sync(path: Path) -> bytes | None:
        if not path.is_file():
            return None
        return path.read_bytes()

    async def delete(self, sha256: str) -> bool:
        """Delete the PDF stored under sha256. Returns whether one was removed."""
        self._ensure_connected()
        return await asyncio.to_thread(self._delete_sync, self._path(sha256))

    @staticmethod
    def _delete_sync(path: Path) -> bool:
        if not path.is_file():
            return False
        path.unlink()
        return True


pdf_store = PdfStore()
