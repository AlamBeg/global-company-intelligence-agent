from __future__ import annotations

import pathlib

from gcia.ingestion.run_ingestion import run as run_ingestion
from gcia.storage.db import SessionLocal
from gcia.storage.models import DiscussionRecord

_FIXTURES = pathlib.Path(__file__).parent / "fixtures"


def test_limit_caps_how_many_raw_items_are_processed():
    """The fixture has 3 items; --limit 1 should only process the first one,
    a real cost/time control for large real-world feeds (e.g. Google News
    RSS returning ~100 items) against a slow provider."""
    feed_uri = (_FIXTURES / "sample_feed.xml").resolve().as_uri()
    run_ingestion("limit-co", "Limit Co", feed_uri, connector_name="rss", limit=1)

    session = SessionLocal()
    try:
        count = (
            session.query(DiscussionRecord)
            .filter(DiscussionRecord.company_id == "limit-co")
            .count()
        )
    finally:
        session.close()

    assert count == 1


def test_no_limit_processes_every_item():
    feed_uri = (_FIXTURES / "sample_feed.xml").resolve().as_uri()
    run_ingestion("nolimit-co", "No Limit Co", feed_uri, connector_name="rss")

    session = SessionLocal()
    try:
        count = (
            session.query(DiscussionRecord)
            .filter(DiscussionRecord.company_id == "nolimit-co")
            .count()
        )
    finally:
        session.close()

    assert count == 3
