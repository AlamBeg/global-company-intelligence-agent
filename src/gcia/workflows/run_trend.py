"""Compares two adjacent time windows of already-ingested, relevant
discussions for a company (FR-020).

This is genuinely computed from real `collected_at` timestamps, not
fabricated - but a single ingestion burst (everything collected within the
same few seconds) has no real time spread to compare, so it will correctly
report ~0% change. That is the honest answer for a fresh demo dataset, not a
bug. Meaningful trends require ingestion spread over real time (recurring
scheduled runs, or backfilled historical `published_at` values).

Usage:
    python -m gcia.workflows.run_trend --company-id acme --window-days 7
"""
from __future__ import annotations

import argparse
import logging
from datetime import datetime, timedelta, timezone

from gcia.agents.lane2.trend import TrendAgent, WindowStats
from gcia.common.config import settings
from gcia.common.context import Budget, RunContext
from gcia.common.model_gateway import ModelGateway, MockProvider
from gcia.storage.db import SessionLocal, init_db
from gcia.storage.models import DiscussionRecord, RelevanceRecord, SentimentRecord

logger = logging.getLogger("gcia.workflows.trend")


def _window_stats(session, company_id: str, start: datetime, end: datetime) -> WindowStats:
    rows = (
        session.query(DiscussionRecord, SentimentRecord)
        .join(RelevanceRecord, RelevanceRecord.discussion_id == DiscussionRecord.discussion_id)
        .join(SentimentRecord, SentimentRecord.discussion_id == DiscussionRecord.discussion_id)
        .filter(
            DiscussionRecord.company_id == company_id,
            RelevanceRecord.is_relevant.is_(True),
            DiscussionRecord.collected_at >= start,
            DiscussionRecord.collected_at < end,
        )
        .all()
    )
    volume = len(rows)
    if volume == 0:
        return WindowStats(volume=0, positive_pct=0.0, negative_pct=0.0, avg_impact=0.0)
    positive = sum(1 for _, s in rows if s.overall_score > 0.1)
    negative = sum(1 for _, s in rows if s.overall_score < -0.1)
    return WindowStats(
        volume=volume,
        positive_pct=(positive / volume) * 100,
        negative_pct=(negative / volume) * 100,
        # Impact scoring is not wired into storage yet (ImpactAgent exists
        # but needs author-influence/reach signals we don't track) - see
        # docs/MVP_ROADMAP.md. avg_impact is 0 until that lands.
        avg_impact=0.0,
    )


def run(company_id: str, window_days: int = 7) -> dict:
    init_db()
    session = SessionLocal()
    try:
        now = datetime.now(timezone.utc)
        current_start = now - timedelta(days=window_days)
        baseline_start = now - timedelta(days=window_days * 2)

        baseline = _window_stats(session, company_id, baseline_start, current_start)
        current = _window_stats(session, company_id, current_start, now)
    finally:
        session.close()

    context = RunContext(
        tenant_id="local",
        budget=Budget(
            max_tokens=settings.gcia_max_tokens_per_run,
            max_cost_usd=settings.gcia_max_cost_usd_per_run,
        ),
        # TrendAgent is tier NONE (pure arithmetic) - the gateway is never
        # actually called, but every agent still takes a RunContext for a
        # uniform interface (MULTI_AGENT_ARCHITECTURE.md).
        model_gateway=ModelGateway(provider=MockProvider()),
    )
    trend = TrendAgent().run((baseline, current), context)

    return {
        "company_id": company_id,
        "window_days": window_days,
        "baseline": {
            "volume": baseline.volume,
            "positive_pct": baseline.positive_pct,
            "negative_pct": baseline.negative_pct,
        },
        "current": {
            "volume": current.volume,
            "positive_pct": current.positive_pct,
            "negative_pct": current.negative_pct,
        },
        "volume_change_pct": trend.volume_change_pct,
        "sentiment_shift": trend.sentiment_shift,
        "impact_change_pct": trend.impact_change_pct,
    }


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--company-id", required=True)
    parser.add_argument("--window-days", type=int, default=7)
    args = parser.parse_args()
    print(run(args.company_id, args.window_days))


if __name__ == "__main__":
    main()
