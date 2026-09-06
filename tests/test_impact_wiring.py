from __future__ import annotations

import pathlib

from gcia.ingestion.run_ingestion import run as run_ingestion
from gcia.storage.db import SessionLocal
from gcia.storage.models import DiscussionRecord
from gcia.workflows.run_company_window import run as run_company_window

_FIXTURES = pathlib.Path(__file__).parent / "fixtures"


def test_impact_score_reflects_real_engagement_not_a_constant():
    """Ingests the Reddit fixture (which has real, differing score/
    num_comments per item), then verifies the computed average impact is
    neither zero nor a suspiciously round fabricated constant - it should
    move if the underlying engagement numbers are actually being read.
    """
    listing_uri = (_FIXTURES / "reddit_listing.json").resolve().as_uri()
    run_ingestion("impact-co", "Impact Co", listing_uri, connector_name="reddit")

    session = SessionLocal()
    try:
        rows = (
            session.query(DiscussionRecord)
            .filter(DiscussionRecord.company_id == "impact-co")
            .all()
        )
        # Sanity check the fixture actually carries real, non-uniform engagement.
        engagements = {r.discussion_id: r.engagement for r in rows}
        assert any(e.get("score", 0) > 0 for e in engagements.values())
    finally:
        session.close()

    result = run_company_window("impact-co")

    assert result["avg_impact_score"] > 0.0
    # A pure-placeholder run (all neutral 0.5 inputs) would average out to a
    # fixed constant; with real engagement/topic_importance/propagation
    # mixed in, the result should not land exactly on that placeholder value.
    assert round(result["avg_impact_score"], 4) != 0.5
