from __future__ import annotations

from datetime import datetime, timezone

from gcia.agents.lane2.dedup import DeduplicationAgent
from gcia.common.context import Budget, RunContext
from gcia.common.model_gateway import ModelGateway, MockProvider
from gcia.schemas.discussion import Discussion


def _discussion(discussion_id: str, content: str) -> Discussion:
    return Discussion(
        discussion_id=discussion_id,
        source_id="rss",
        original_url=f"https://example.com/{discussion_id}",
        platform="rss",
        source_type="news",
        collected_at=datetime.now(timezone.utc),
        content=content,
        raw_record_id=f"rss:{discussion_id}",
        content_hash=discussion_id,
    )


def test_near_duplicate_articles_are_clustered_not_dropped():
    context = RunContext(
        tenant_id="test",
        budget=Budget(max_tokens=10_000, max_cost_usd=1.0),
        model_gateway=ModelGateway(provider=MockProvider()),
    )
    original = _discussion(
        "a", "The company announced record quarterly earnings today in a press release."
    )
    syndicated = _discussion(
        "b", "The company announced record quarterly earnings today in a press release."
    )
    unrelated = _discussion(
        "c", "A totally different story about unrelated weather events in another region."
    )

    clusters = DeduplicationAgent().run([original, syndicated, unrelated], context)

    assert len(clusters) == 1
    assert set(clusters[0].member_discussion_ids) == {"a", "b"}
    # Source records for both members must remain retrievable - clustering
    # marks derivatives, it never deletes them (FR-016 / DATA_ARCHITECTURE.md).
    assert clusters[0].canonical_discussion_id in {"a", "b"}
