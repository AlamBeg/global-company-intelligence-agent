from __future__ import annotations

from datetime import datetime, timezone

from gcia.agents.lane1.relevance import RelevanceAgent
from gcia.common.context import Budget, RunContext
from gcia.common.model_gateway import ModelGateway, MockProvider
from gcia.schemas.company import Company
from gcia.schemas.discussion import Discussion


def _discussion() -> Discussion:
    return Discussion(
        discussion_id="d1",
        source_id="rss",
        original_url="https://example.com/a",
        platform="rss",
        source_type="news",
        collected_at=datetime.now(timezone.utc),
        content="Acme Corp announced a new product today.",
        raw_record_id="rss:abc123",
        content_hash="hash",
    )


def test_low_confidence_escalates_from_small_to_large_tier():
    # A low-confidence response should trigger RelevanceAgent's escalation
    # cascade: try SMALL first, only call LARGE when confidence is weak.
    provider = MockProvider(fixed_response={"is_relevant": True, "reason": "match", "confidence": 0.3})
    gateway = ModelGateway(provider=provider)
    context = RunContext(
        tenant_id="test",
        budget=Budget(max_tokens=10_000, max_cost_usd=1.0),
        model_gateway=gateway,
    )
    company = Company(company_id="acme", canonical_name="Acme Corp")

    RelevanceAgent().run((_discussion(), company), context)

    # Two distinct calls (small, then escalated large) - not one.
    assert provider.calls == 2
    assert context.budget.spent_tokens > 0


def test_high_confidence_does_not_escalate():
    provider = MockProvider(fixed_response={"is_relevant": True, "reason": "match", "confidence": 0.95})
    gateway = ModelGateway(provider=provider)
    context = RunContext(
        tenant_id="test",
        budget=Budget(max_tokens=10_000, max_cost_usd=1.0),
        model_gateway=gateway,
    )
    company = Company(company_id="acme", canonical_name="Acme Corp")

    RelevanceAgent().run((_discussion(), company), context)

    assert provider.calls == 1


def test_repeated_calls_with_same_cache_key_are_free():
    provider = MockProvider()
    gateway = ModelGateway(provider=provider)
    context = RunContext(
        tenant_id="test",
        budget=Budget(max_tokens=10_000, max_cost_usd=1.0),
        model_gateway=gateway,
    )

    gateway.complete(
        tier="small",
        system="s",
        prompt="p",
        schema_hint="{}",
        context=context,
        cache_key="fixed-key",
    )
    gateway.complete(
        tier="small",
        system="s",
        prompt="p",
        schema_hint="{}",
        context=context,
        cache_key="fixed-key",
    )

    assert provider.calls == 1
