"""Auth / access-control regression tests for the LakeFlow backend (no Qdrant or LLM needed)."""
import pytest
from fastapi.testclient import TestClient

from lakeflow.core import config
from lakeflow.core.security import create_access_token
from lakeflow.main import app

client = TestClient(app)


def _bearer(username: str) -> dict:
    return {"Authorization": f"Bearer {create_access_token({'sub': username})}"}


# (method, path) pairs that must reject anonymous callers
PROTECTED = [
    ("POST", "/pipeline/run/step0"),
    ("GET", "/pipeline/folders/step0"),
    ("GET", "/pipeline/embed-models"),
    ("POST", "/inbox/upload"),
    ("GET", "/inbox/domains"),
    ("GET", "/inbox/list"),
    ("POST", "/system/data-path"),
    ("POST", "/system/create-zones"),
    ("GET", "/system/config"),
    ("GET", "/system/zones-status"),
    ("GET", "/system/health-detail"),
    ("POST", "/search/embed"),
    ("POST", "/search/semantic"),
    ("POST", "/search/qa"),
    ("GET", "/qdrant/collections"),
    ("GET", "/admin/users"),
    ("POST", "/admission_agent/v1/ask"),
    ("GET", "/admission_agent/v1/data"),
    ("POST", "/library_document_agent/v1/ask"),
    ("POST", "/library_regulation_agent/v1/ask"),
    ("POST", "/research_khcn_regulation_agent/v1/ask"),
]


@pytest.mark.parametrize("method,path", PROTECTED)
def test_anonymous_requests_are_rejected(method, path):
    assert client.request(method, path).status_code == 401


@pytest.mark.parametrize("path", ["/health", "/system/locales", "/system/data-path", "/admission_agent/v1/metadata"])
def test_public_endpoints_stay_public(path):
    assert client.get(path).status_code == 200


@pytest.mark.parametrize(
    "method,path",
    [
        ("GET", "/admin/users"),
        ("DELETE", "/admin/users/someone/messages"),
        ("POST", "/system/create-zones"),
        ("POST", "/pipeline/run/step0"),
    ],
)
def test_non_admin_gets_403_not_500(method, path):
    assert client.request(method, path, headers=_bearer("not-admin")).status_code == 403


def test_login_and_admin_access():
    resp = client.post("/auth/login", json={"username": "admin", "password": "admin123"})
    assert resp.status_code == 200
    token = resp.json()["access_token"]
    assert client.get("/auth/me", headers={"Authorization": f"Bearer {token}"}).json() == {"username": "admin"}
    assert client.get("/system/config", headers={"Authorization": f"Bearer {token}"}).status_code == 200


def test_wrong_password_rejected():
    assert client.post("/auth/login", json={"username": "admin", "password": "nope"}).status_code == 401


def test_jwt_secret_is_never_the_public_default():
    assert config.JWT_SECRET_KEY != "DEV_ONLY_CHANGE_ME_IMMEDIATELY"
    assert len(config.JWT_SECRET_KEY) >= 32


def test_cors_wildcard_has_no_credentials():
    resp = client.options(
        "/health",
        headers={"Origin": "https://evil.example", "Access-Control-Request-Method": "GET"},
    )
    assert resp.headers.get("access-control-allow-credentials") != "true"


def test_qdrant_url_allowlist(monkeypatch):
    assert config.get_qdrant_url("http://other:6333")  # no allowlist -> accepted (backward compatible)
    monkeypatch.setattr(config, "QDRANT_ALLOWED_URLS", {"http://research:8010"})
    assert config.get_qdrant_url("research:8010/") == "http://research:8010"
    assert config.get_qdrant_url(None) == config.QDRANT_URL
    with pytest.raises(config.QdrantUrlNotAllowedError):
        config.get_qdrant_url("http://169.254.169.254")


def test_disallowed_qdrant_url_is_400(monkeypatch):
    monkeypatch.setattr(config, "QDRANT_ALLOWED_URLS", {"http://research:8010"})
    resp = client.get("/qdrant/collections", params={"qdrant_url": "http://evil:6333"}, headers=_bearer("admin"))
    assert resp.status_code == 400
