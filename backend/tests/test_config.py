import pytest

from src import config


def test_postgres_dsn_percent_encodes_components(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("STUDIO_POSTGRES_USER", "studio")
    monkeypatch.setenv("STUDIO_POSTGRES_PASSWORD", "pa@ss:word")
    monkeypatch.setenv("STUDIO_POSTGRES_DB", "studio db")
    monkeypatch.delenv("STUDIO_POSTGRES_HOST", raising=False)
    monkeypatch.delenv("STUDIO_POSTGRES_PORT", raising=False)

    assert config.postgres_dsn() == (
        "postgresql://studio:pa%40ss%3Aword@studio_postgres:5432/studio%20db"
    )


def test_postgres_dsn_uses_host_and_port_overrides(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("STUDIO_POSTGRES_USER", "u")
    monkeypatch.setenv("STUDIO_POSTGRES_PASSWORD", "p")
    monkeypatch.setenv("STUDIO_POSTGRES_DB", "d")
    monkeypatch.setenv("STUDIO_POSTGRES_HOST", "localhost")
    monkeypatch.setenv("STUDIO_POSTGRES_PORT", "5433")

    assert config.postgres_dsn() == "postgresql://u:p@localhost:5433/d"


def test_postgres_dsn_requires_components(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("STUDIO_POSTGRES_USER", raising=False)

    with pytest.raises(
        RuntimeError,
        match="STUDIO_POSTGRES_USER",
    ):
        _ = config.postgres_dsn()
