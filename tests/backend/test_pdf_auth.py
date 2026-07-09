import pytest
from fastapi import HTTPException

from backend.endpoints import auth as auth_module


class _FakeRequest:
    def __init__(self, headers=None, session=None):
        self.headers = headers or {}
        self.session = session or {}


def _install_api_keys(monkeypatch, keys: dict[str, str]):
    monkeypatch.setattr(auth_module, "_API_KEYS", keys)


# -------------------------------------------------------
# require_api_key
# -------------------------------------------------------

def test_require_api_key_accepts_a_configured_key_and_returns_its_app_name(monkeypatch):
    _install_api_keys(monkeypatch, {"scepa-rs": "secret-key"})
    request = _FakeRequest(headers={"authorization": "Bearer secret-key"})

    assert auth_module.require_api_key(request) == "scepa-rs"


def test_require_api_key_rejects_an_unknown_key(monkeypatch):
    _install_api_keys(monkeypatch, {"scepa-rs": "secret-key"})
    request = _FakeRequest(headers={"authorization": "Bearer wrong-key"})

    with pytest.raises(HTTPException) as exc:
        auth_module.require_api_key(request)
    assert exc.value.status_code == 401


def test_require_api_key_rejects_a_missing_or_malformed_header(monkeypatch):
    _install_api_keys(monkeypatch, {"scepa-rs": "secret-key"})

    with pytest.raises(HTTPException):
        auth_module.require_api_key(_FakeRequest())
    with pytest.raises(HTTPException):
        auth_module.require_api_key(_FakeRequest(headers={"authorization": "secret-key"}))


# -------------------------------------------------------
# get_current_user_or_api_key
# -------------------------------------------------------

def test_get_current_user_or_api_key_accepts_a_browser_session(monkeypatch):
    _install_api_keys(monkeypatch, {})
    request = _FakeRequest(session={"user": {"sub": "user-1"}})

    assert auth_module.get_current_user_or_api_key(request) == "user-1"


def test_get_current_user_or_api_key_accepts_an_api_key_without_a_session(monkeypatch):
    _install_api_keys(monkeypatch, {"scepa-rs": "secret-key"})
    request = _FakeRequest(headers={"authorization": "Bearer secret-key"})

    assert auth_module.get_current_user_or_api_key(request) == "scepa-rs"


def test_get_current_user_or_api_key_rejects_neither(monkeypatch):
    _install_api_keys(monkeypatch, {"scepa-rs": "secret-key"})

    with pytest.raises(HTTPException) as exc:
        auth_module.get_current_user_or_api_key(_FakeRequest())
    assert exc.value.status_code == 401
