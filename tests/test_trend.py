from __future__ import annotations

import pathlib
from datetime import datetime, timedelta, timezone

from gcia.ingestion.run_ingestion import run as run_ingestion
from gcia.storage.db import SessionLocal
from gcia.storage.models import DiscussionRecord
from gcia.workflows.run_trend import run as run_trend

_FIXTURES = pathlib.Path(__file__).parent / "fixtures"


def test_trend_reflects_real_backdated_timestamps():
    """Ingests 3 discussions (all collected "now"), then manually backdates
    2 of them into the prior window to simulate real historical spread -
    proving TrendAgent's volume_change_pct is computed from actual
    timestamps, not fabricated. 1 item in the current 7-day window vs 2 in
    the prior 7-day window is a real -50% volume change.
    """
    feed_uri = (_FIXTURES / "sample_feed.xml").resolve().as_uri()
    run_ingestion("trend-co", "Trend Co", feed_uri, connector_name="rss")

    session = SessionLocal()
    try:
        discussions = (
            session.query(DiscussionRecord)
            .filter(DiscussionRecord.company_id == "trend-co")
            .order_by(DiscussionRecord.discussion_id)
            .all()
        )
        assert len(discussions) == 3
        backdated_time = datetime.now(timezone.utc) - timedelta(days=10)
        for record in discussions[:2]:
            record.collected_at = backdated_time
        session.commit()
    finally:
        session.close()

    result = run_trend("trend-co", window_days=7)

    assert result["baseline"]["volume"] == 2
    assert result["current"]["volume"] == 1
    assert result["volume_change_pct"] == -50.0
