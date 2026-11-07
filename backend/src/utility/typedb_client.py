"""Minimal read-only TypeDB HTTP client.

POC(fcose): introduced for the FCose mock graph export. The same client is
intended for the upcoming read-only FastMCP server, so the transaction type is
hardcoded and there is deliberately no write or schema query path.

Only the endpoints needed for reads are used:

* ``POST /v1/signin`` to obtain a short-lived token
* ``POST /v1/query`` with ``transactionType: "read"``

The client uses the standard library so it runs on the backend's Python 3.15
environment, which has no ``typedb-driver`` wheel.
"""

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any

READ_TRANSACTION = "read"  # POC(fcose): never make this configurable.

DEFAULT_TIMEOUT_SECONDS = 30


class TypeDBError(RuntimeError):
    """A TypeDB request failed or returned an unusable response."""


@dataclass(frozen=True)
class TypeDBConfig:
    """Connection settings for a local TypeDB CE instance."""

    url: str = "http://localhost:8000"
    database: str = "bookstore"
    username: str = "bookstore"
    password: str = "password"

    @classmethod
    def from_env(cls) -> "TypeDBConfig":
        return cls(
            url=os.environ.get("TYPEDB_URL", cls.url),
            database=os.environ.get("TYPEDB_DATABASE", cls.database),
            username=os.environ.get("TYPEDB_USERNAME", cls.username),
            password=os.environ.get("TYPEDB_PASSWORD", cls.password),
        )


class TypeDBReadClient:
    """Signs in once and issues read queries against a single database."""

    def __init__(
        self,
        config: TypeDBConfig | None = None,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
    ) -> None:
        self._config = config or TypeDBConfig.from_env()
        self._timeout = timeout
        self._token: str | None = None

    @property
    def config(self) -> TypeDBConfig:
        return self._config

    def signin(self) -> str:
        """Authenticate and cache the returned token."""
        payload = {
            "username": self._config.username,
            "password": self._config.password,
        }
        response = self._post("/v1/signin", payload)
        token = response.get("token")
        if not isinstance(token, str):
            raise TypeDBError("signin response did not contain a token")
        self._token = token
        return token

    def query(self, typeql: str) -> dict[str, Any]:
        """Run one read query and return the full JSON response.

        A stale token is retried once after signing in again, because tokens
        expire after roughly an hour.
        """
        body = {
            "databaseName": self._config.database,
            "transactionType": READ_TRANSACTION,
            "query": typeql,
            "commit": False,
        }
        try:
            return self._post("/v1/query", body, token=self._require_token())
        except _Unauthorized:
            self.signin()
            return self._post("/v1/query", body, token=self._require_token())

    def fetch_documents(self, typeql: str) -> list[dict[str, Any]]:
        """Run a fetch query and return the list of documents."""
        response = self.query(typeql)
        answer_type = response.get("answerType")
        if answer_type != "conceptDocuments":
            raise TypeDBError(
                f"expected conceptDocuments, got {answer_type!r}: {typeql[:120]}"
            )
        answers = response.get("answers") or []
        if not isinstance(answers, list):
            raise TypeDBError("query response answers was not a list")
        return answers

    def _require_token(self) -> str:
        if self._token is None:
            return self.signin()
        return self._token

    def _post(
        self,
        path: str,
        payload: dict[str, Any],
        token: str | None = None,
    ) -> dict[str, Any]:
        url = f"{self._config.url.rstrip('/')}{path}"
        headers = {"content-type": "application/json"}
        if token is not None:
            headers["authorization"] = f"Bearer {token}"
        request = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self._timeout) as response:
                raw = response.read().decode("utf-8")
        except urllib.error.HTTPError as error:
            detail = error.read().decode("utf-8", errors="replace")
            if error.code == 401:
                raise _Unauthorized(detail) from error
            raise TypeDBError(f"{path} failed with {error.code}: {detail}") from error
        except urllib.error.URLError as error:
            raise TypeDBError(
                f"cannot reach TypeDB at {url}: {error.reason}"
            ) from error

        try:
            result = json.loads(raw)
        except json.JSONDecodeError as error:
            raise TypeDBError(f"{path} returned invalid JSON: {raw[:200]}") from error
        if not isinstance(result, dict):
            raise TypeDBError(f"{path} returned unexpected JSON: {raw[:200]}")
        return result


class _Unauthorized(TypeDBError):
    """Internal marker for a 401 response so the caller can re-authenticate."""
