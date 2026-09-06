"""One-shot Lane 2 batch run for a single company: dedup, topic clustering,
narrative clustering, credibility, impact, and risk - over everything Lane 1
has already ingested and marked relevant.

This is the manual stand-in for the Orchestrator starting a Lane 2 workflow
run - see MULTI_AGENT_ARCHITECTURE.md "Lane 2 - Batch, per company/window".
Run it after `gcia.ingestion.run_ingestion` has populated at least one
company.

TrendAgent is intentionally not wired here: it compares two time windows,
and a single run of this script only has one snapshot. See
`workflows/run_trend.py`, which does use real timestamps across windows.

Usage:
    python -m gcia.workflows.run_company_window --company-id acme
"""
from __future__ import annotations

import argparse
import logging

from gcia.agents.lane2.clustering import naive_topic_clusters
from gcia.agents.lane2.credibility import CredibilityAgent, CredibilityInputs
from gcia.agents.lane2.dedup import DeduplicationAgent
from gcia.agents.lane2.impact import ImpactAgent, ImpactInputs
from gcia.agents.lane2.narrative import NarrativeAgent
from gcia.agents.lane2.risk import RiskAgent
from gcia.agents.lane2.topic import TopicAgent
from gcia.common.config import settings
from gcia.common.context import Budget, RunContext
from gcia.common.model_gateway import AnthropicProvider, ModelGateway, MockProvider
from gcia.storage import repository
from gcia.storage.db import SessionLocal, init_db

logger = logging.getLogger("gcia.workflows.company_window")

# Used only when no ANTHROPIC_API_KEY is configured - placeholder, not real
# analysis, same convention as gcia.ingestion.run_ingestion.
_NO_KEY_FALLBACK_RESPONSE = {
    "label": "unlabeled (no ANTHROPIC_API_KEY configured)",
    "confidence": 0.5,
    "category": "reputation",
    "summary": "placeholder - no ANTHROPIC_API_KEY configured",
    "severity": 0.0,
    "momentum": 0.0,
    "affected_segments": [],
}

# Inputs we cannot yet derive from real signals (need author-history
# tracking, cross-source fact corroboration, follower/reach data, etc.) -
# held at a neutral midpoint rather than fabricated, and documented as such
# (docs/AI_SCORING_MODEL.md: neither credibility nor impact is a truth score).
_NEUTRAL_PLACEHOLDER = 0.5

# Real engagement magnitude above which engagement_norm saturates at 1.0.
# Illustrative only - not tuned against real data.
_ENGAGEMENT_SATURATION_POINT = 100.0


def run(company_id: str) -> dict:
    init_db()

    if settings.anthropic_api_key:
        provider = AnthropicProvider()
    else:
        provider = MockProvider(fixed_response=_NO_KEY_FALLBACK_RESPONSE)
        logger.warning(
            "ANTHROPIC_API_KEY not set - topic/narrative labels and risk summaries will be "
            "placeholders, not real model output. Set it in .env for real analysis."
        )

    context = RunContext(
        tenant_id="local",
        budget=Budget(
            max_tokens=settings.gcia_max_tokens_per_run,
            max_cost_usd=settings.gcia_max_cost_usd_per_run,
        ),
        model_gateway=ModelGateway(provider=provider),
    )

    session = SessionLocal()
    try:
        discussions = repository.list_relevant_discussions(session, company_id)
        if not discussions:
            logger.warning(
                "no relevant discussions found for %s - run ingestion first", company_id
            )
            return {"topics": 0, "narratives": 0, "risks": 0, "duplicate_clusters": 0}

        repository.clear_lane2_outputs(session, company_id)

        duplicate_clusters = DeduplicationAgent().run(discussions, context)
        for cluster in duplicate_clusters:
            # cluster_id as built by DeduplicationAgent is scoped only to a
            # discussion_id, which is not unique across companies - rescope
            # here where company context is known (same rationale as
            # evidence_id/claim_id in gcia.ingestion.run_ingestion).
            cluster.cluster_id = f"{company_id}:{cluster.cluster_id}"
            repository.save_duplicate_cluster(session, company_id, cluster)

        # Non-canonical duplicate members are excluded from topic/risk input:
        # a syndicated copy should not count as a second independent opinion
        # (FR-016).
        duplicate_member_ids = {
            member_id
            for cluster in duplicate_clusters
            for member_id in cluster.member_discussion_ids
            if member_id != cluster.canonical_discussion_id
        }
        canonical_discussions = [
            d for d in discussions if d.discussion_id not in duplicate_member_ids
        ]

        # Real signals computed before Credibility/Impact so both can use
        # them: originality from the dedup ratio, corroboration from
        # cross-platform spread. The rest of Credibility's inputs stay at a
        # documented neutral placeholder until author-history and
        # fact-corroboration tracking exist.
        duplicate_discussions_grouped = sum(
            len(c.member_discussion_ids) for c in duplicate_clusters
        )
        originality = 1 - (duplicate_discussions_grouped / len(discussions)) if discussions else 1.0
        platforms = {d.platform for d in canonical_discussions}
        corroboration = len(platforms) / len(canonical_discussions) if canonical_discussions else 0.0

        credibility_score = CredibilityAgent().run(
            CredibilityInputs(
                source_history_score=_NEUTRAL_PLACEHOLDER,
                author_identity_consistency=_NEUTRAL_PLACEHOLDER,
                evidence_quality=_NEUTRAL_PLACEHOLDER,
                originality=originality,
                specialization=_NEUTRAL_PLACEHOLDER,
                engagement_authenticity=_NEUTRAL_PLACEHOLDER,
                corroboration=corroboration,
            ),
            context,
        )
        repository.update_company_credibility(session, company_id, credibility_score)

        topic_clusters = naive_topic_clusters(canonical_discussions)
        cluster_size_by_discussion_id = {
            d.discussion_id: len(cluster) for cluster in topic_clusters for d in cluster
        }
        for cluster in topic_clusters:
            # topic_id/narrative_id as built by the agents are scoped only
            # to a discussion_id, not unique across companies - rescope here.
            topic = TopicAgent().run(cluster, context)
            topic.company_id = company_id
            topic.topic_id = f"{company_id}:{topic.topic_id}"
            repository.save_topic(session, company_id, topic)

            narrative = NarrativeAgent().run(cluster, context)
            narrative.company_id = company_id
            narrative.narrative_id = f"{company_id}:{narrative.narrative_id}"
            repository.save_narrative(session, company_id, narrative)

        risk = RiskAgent().run(canonical_discussions, context)
        risk.company_id = company_id
        risk.risk_id = f"{company_id}:{risk.risk_id}"
        repository.save_risk(session, company_id, risk)

        # Impact: engagement, topic_importance, and propagation are real
        # signals derived from this run's own data; source_credibility reuses
        # the score just computed above. reach/author_influence/velocity have
        # no real signal source yet (no follower counts or author history, no
        # multi-window baseline here - see run_trend.py for that) and stay at
        # the same documented neutral placeholder as Credibility's gaps.
        propagated_canonical_ids = {c.canonical_discussion_id for c in duplicate_clusters}
        impact_scores = []
        for d in canonical_discussions:
            engagement_magnitude = d.engagement.get("score", 0) + d.engagement.get("num_comments", 0)
            engagement_norm = min(1.0, engagement_magnitude / _ENGAGEMENT_SATURATION_POINT)
            topic_importance = (
                cluster_size_by_discussion_id.get(d.discussion_id, 1) / len(canonical_discussions)
                if canonical_discussions
                else 0.0
            )
            propagation = 1.0 if d.discussion_id in propagated_canonical_ids else 0.0

            impact_scores.append(
                ImpactAgent().run(
                    ImpactInputs(
                        reach=_NEUTRAL_PLACEHOLDER,
                        engagement=engagement_norm,
                        author_influence=_NEUTRAL_PLACEHOLDER,
                        source_credibility=credibility_score,
                        topic_importance=topic_importance,
                        velocity=_NEUTRAL_PLACEHOLDER,
                        propagation=propagation,
                        originality=_NEUTRAL_PLACEHOLDER,
                    ),
                    context,
                )
            )
        avg_impact_score = sum(impact_scores) / len(impact_scores) if impact_scores else 0.0
        repository.update_company_impact(session, company_id, avg_impact_score)
    finally:
        session.close()

    result = {
        "topics": len(topic_clusters),
        "narratives": len(topic_clusters),
        "risks": 1,
        "duplicate_clusters": len(duplicate_clusters),
        "credibility_score": credibility_score,
        "avg_impact_score": avg_impact_score,
    }
    logger.info(
        "lane 2 complete for %s: %d topic(s)/narrative(s), 1 risk summary, "
        "%d duplicate cluster(s), credibility %.2f, avg impact %.2f",
        company_id,
        result["topics"],
        result["duplicate_clusters"],
        credibility_score,
        avg_impact_score,
    )
    return result


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--company-id", required=True)
    args = parser.parse_args()
    print(run(args.company_id))


if __name__ == "__main__":
    main()
