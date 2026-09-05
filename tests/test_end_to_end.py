from __future__ import annotations

import pathlib

from fastapi.testclient import TestClient

from gcia.api.main import app
from gcia.common.config import settings
from gcia.ingestion.run_ingestion import run as run_ingestion
from gcia.workflows.run_company_window import run as run_company_window

_FIXTURES = pathlib.Path(__file__).parent / "fixtures"


def test_full_pipeline_populates_company_summary_and_api():
    """Connector -> Lane 1 (all agents) -> Lane 2 (all agents) -> API -> Ask,
    against the isolated test database (see conftest.py). Runs entirely in
    placeholder mode (no ANTHROPIC_API_KEY in the test environment) - this
    proves the pipeline shape and storage wiring, not real analysis quality.
    """
    settings.gcia_api_keys = ""
    feed_uri = (_FIXTURES / "sample_feed.xml").resolve().as_uri()

    ingested = run_ingestion("e2e-co", "E2E Co", feed_uri, connector_name="rss")
    assert ingested == 3

    lane2_result = run_company_window("e2e-co")
    assert lane2_result["topics"] >= 1
    assert lane2_result["risks"] == 1
    assert lane2_result["credibility_score"] is not None

    client = TestClient(app)
    res = client.get("/v1/companies/e2e-co")
    assert res.status_code == 200
    data = res.json()
    assert data["discussion_count"] == 3
    assert data["credibility_score"] is not None
    assert len(data["topics"]) >= 1
    assert len(data["narratives"]) >= 1
    # Every evidence item must carry its original URL through untouched (FR-005).
    assert all(e["original_url"] for e in data["evidence"])

    ask_res = client.post("/v1/companies/e2e-co/ask", json={"question": "What is being said?"})
    assert ask_res.status_code == 200
    body = ask_res.json()
    assert "answer" in body and "citations" in body and "confidence" in body


def test_ask_returns_404_with_no_evidence():
    client = TestClient(app)
    res = client.post("/v1/companies/nonexistent-co/ask", json={"question": "anything?"})
    assert res.status_code == 404
