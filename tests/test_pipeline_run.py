from __future__ import annotations

import pathlib
import time

from fastapi.testclient import TestClient

from gcia.api.main import app
from gcia.common.config import settings

_FIXTURES = pathlib.Path(__file__).parent / "fixtures"


def _poll_until_finished(client: TestClient, run_id: str, timeout_seconds: float = 10.0) -> dict:
    deadline = time.time() + timeout_seconds
    run = {}
    while time.time() < deadline:
        run = client.get(f"/v1/runs/{run_id}").json()
        if run["status"] != "running":
            return run
        time.sleep(0.05)
    raise AssertionError(f"run did not finish within {timeout_seconds}s: {run}")


def test_start_run_and_poll_reaches_done_with_every_agent_reporting():
    settings.gcia_api_keys = ""
    feed_uri = (_FIXTURES / "sample_feed.xml").resolve().as_uri()
    client = TestClient(app)

    res = client.post(
        "/v1/runs",
        json={"company_name": "Pipeline Co", "company_id": "pipeline-co", "feed_url": feed_uri},
    )
    assert res.status_code == 200
    run_id = res.json()["run_id"]
    assert res.json()["company_id"] == "pipeline-co"

    run = _poll_until_finished(client, run_id)
    assert run["status"] == "done"
    assert run["error"] is None
    # Lane 1 (per-item) and Lane 2 (per-company) agents both reported in.
    for agent in ("Normalization", "Relevance", "Sentiment"):
        assert run["agents"][agent]["status"] == "done"
    for agent in ("Deduplication", "Credibility", "Risk"):
        assert run["agents"][agent]["status"] == "done"
    assert len(run["events"]) > 0


def test_company_id_defaults_to_a_slug_of_the_company_name():
    settings.gcia_api_keys = ""
    feed_uri = (_FIXTURES / "sample_feed.xml").resolve().as_uri()
    client = TestClient(app)

    res = client.post("/v1/runs", json={"company_name": "Weird & Co!!", "feed_url": feed_uri})
    assert res.status_code == 200
    assert res.json()["company_id"] == "weird-co"


def test_unknown_run_id_returns_404():
    settings.gcia_api_keys = ""
    client = TestClient(app)
    res = client.get("/v1/runs/does-not-exist")
    assert res.status_code == 404


def test_starting_a_run_requires_analyst_role():
    settings.gcia_api_keys = "secret-viewer:viewer,secret-analyst:analyst"
    try:
        client = TestClient(app)
        res = client.post(
            "/v1/runs",
            json={"company_name": "RBAC Co"},
            headers={"X-API-Key": "secret-viewer"},
        )
        assert res.status_code == 403
    finally:
        settings.gcia_api_keys = ""
