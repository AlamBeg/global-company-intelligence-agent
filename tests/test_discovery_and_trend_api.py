from __future__ import annotations

import pathlib

from fastapi.testclient import TestClient

from gcia.api.main import app
from gcia.common.config import settings
from gcia.ingestion.run_ingestion import run as run_ingestion

_FIXTURES = pathlib.Path(__file__).parent / "fixtures"


def test_discover_queries_endpoint_returns_suggestions():
    settings.gcia_api_keys = ""
    client = TestClient(app)
    res = client.post(
        "/v1/companies/acme/discover-queries",
        json={"canonical_name": "Acme Corp", "known_aliases": ["ACME"], "known_tickers": ["ACM"]},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["company_id"] == "acme"
    assert "suggested_queries" in body


def test_trend_endpoint_reflects_ingested_data():
    settings.gcia_api_keys = ""
    feed_uri = (_FIXTURES / "sample_feed.xml").resolve().as_uri()
    run_ingestion("trend-api-co", "Trend API Co", feed_uri, connector_name="rss")

    client = TestClient(app)
    res = client.get("/v1/companies/trend-api-co/trend?window_days=7")
    assert res.status_code == 200
    body = res.json()
    # All 3 items were just ingested "now", so they land in the current
    # window and the baseline window is genuinely empty - a real +100%-style
    # signal from real timestamps, not a fabricated number.
    assert body["current"]["volume"] == 3
    assert body["baseline"]["volume"] == 0
