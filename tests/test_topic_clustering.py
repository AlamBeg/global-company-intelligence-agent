from __future__ import annotations

from datetime import datetime, timezone

from gcia.agents.lane2.clustering import naive_topic_clusters
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


def test_related_but_non_identical_discussions_cluster_together():
    a = _discussion("a", "Acme Corp customer support wait times are frustrating this week")
    b = _discussion("b", "Acme Corp support wait times remain a frustrating customer issue")
    unrelated = _discussion("c", "Local weather forecast calls for rain this weekend")

    clusters = naive_topic_clusters([a, b, unrelated])
    cluster_ids = [{d.discussion_id for d in cluster} for cluster in clusters]

    assert {"a", "b"} in cluster_ids
    assert any(cluster == {"c"} for cluster in cluster_ids)


def test_every_discussion_appears_in_exactly_one_cluster():
    discussions = [_discussion(str(i), f"unique content number {i} about something") for i in range(5)]
    clusters = naive_topic_clusters(discussions)

    seen = [d.discussion_id for cluster in clusters for d in cluster]
    assert sorted(seen) == sorted(d.discussion_id for d in discussions)
    assert len(seen) == len(set(seen))
