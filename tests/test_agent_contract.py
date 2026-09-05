from __future__ import annotations

from datetime import datetime, timezone

from gcia.agents.lane1.normalization import NormalizationAgent
from gcia.common.context import Budget, RunContext
from gcia.common.model_gateway import ModelGateway, MockProvider
from gcia.schemas.discussion import RawRecord


def _context() -> RunContext:
    return RunContext(
        tenant_id="test",
        budget=Budget(max_tokens=10_000, max_cost_usd=1.0),
        model_gateway=ModelGateway(provider=MockProvider()),
    )


def test_normalization_is_deterministic():
    raw = RawRecord(
        platform="rss",
        source_native_id="abc123",
        original_url="https://example.com/a",
        collected_at=datetime.now(timezone.utc),
        content="Example content about a company.",
    )
    agent = NormalizationAgent()
    context = _context()

    first = agent.run(raw, context)
    second = agent.run(raw, context)

    assert first.discussion_id == second.discussion_id
    assert first.content_hash == second.content_hash
    assert first.original_url == "https://example.com/a"


def test_normalization_never_invents_a_url():
    raw = RawRecord(
        platform="rss",
        source_native_id="no-url-item",
        original_url=None,
        collected_at=datetime.now(timezone.utc),
        content="Content with no stable source URL.",
    )
    discussion = NormalizationAgent().run(raw, _context())

    assert discussion.original_url is None
    assert discussion.url_status == "unavailable"
