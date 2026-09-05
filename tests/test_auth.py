from __future__ import annotations

from fastapi.testclient import TestClient

from gcia.api.main import app
from gcia.common.config import settings


def test_no_keys_configured_allows_access_for_local_dev():
    settings.gcia_api_keys = ""
    client = TestClient(app)
    res = client.get("/v1/companies/does-not-exist")
    assert res.status_code == 404  # reached the handler, not blocked by auth


def test_missing_key_is_rejected_once_keys_are_configured():
    settings.gcia_api_keys = "secret-analyst:analyst,secret-admin:admin"
    try:
        client = TestClient(app)
        res = client.get("/v1/evidence/whatever")
        assert res.status_code == 401
    finally:
        settings.gcia_api_keys = ""


def test_viewer_key_cannot_access_analyst_only_route():
    settings.gcia_api_keys = "secret-viewer:viewer,secret-analyst:analyst"
    try:
        client = TestClient(app)
        res = client.get("/v1/evidence/whatever", headers={"X-API-Key": "secret-viewer"})
        assert res.status_code == 403
    finally:
        settings.gcia_api_keys = ""


def test_analyst_key_can_access_analyst_only_route():
    settings.gcia_api_keys = "secret-analyst:analyst"
    try:
        client = TestClient(app)
        res = client.get("/v1/evidence/whatever", headers={"X-API-Key": "secret-analyst"})
        # 404 (not found), not 401/403, proves it passed auth and reached the handler.
        assert res.status_code == 404
    finally:
        settings.gcia_api_keys = ""


def test_viewer_key_can_access_viewer_route():
    settings.gcia_api_keys = "secret-viewer:viewer"
    try:
        client = TestClient(app)
        res = client.get("/v1/companies/does-not-exist", headers={"X-API-Key": "secret-viewer"})
        assert res.status_code == 404
    finally:
        settings.gcia_api_keys = ""
