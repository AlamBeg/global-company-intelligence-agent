"""One-shot Lane 1 ingestion for a single (company, feed) pair.

This is the manual stand-in for the Orchestrator starting a Lane 1 run - see
MULTI_AGENT_ARCHITECTURE.md "Orchestrator responsibilities in practice". It
wires the full Lane 1 agent set: connector -> Normalization -> Language ->
Geography -> Verification -> Relevance -> Sentiment -> Emotion -> Intent ->
Claim -> storage. Every agent that is coded and cheap enough to run at
per-item volume runs here; nothing is left orphaned.

Usage:
    python -m gcia.ingestion.run_ingestion \\
        --company-id acme --company-name "Acme Corp" \\
        --connector rss --feed-url https://example.com/feed.xml
"""
from __future__ import annotations

import argparse
import logging
from datetime import datetime, timezone

from gcia.agents.lane1.claim import ClaimAgent
from gcia.agents.lane1.emotion import EmotionAgent
from gcia.agents.lane1.geography import GeographyAgent
from gcia.agents.lane1.intent import IntentAgent
from gcia.agents.lane1.language import LanguageAgent
from gcia.agents.lane1.normalization import NormalizationAgent
from gcia.agents.lane1.relevance import RelevanceAgent
from gcia.agents.lane1.sentiment import SentimentAgent
from gcia.agents.lane3.verification import VerificationAgent
from gcia.common.config import settings
from gcia.common.context import Budget, RunContext
from gcia.common.model_gateway import ModelGateway, resolve_provider
from gcia.connectors.reddit_public import RedditPublicConnector
from gcia.connectors.rss_news import RssNewsConnector
from gcia.schemas.company import Company
from gcia.schemas.evidence import Evidence
from gcia.storage import repository
from gcia.storage.db import SessionLocal, init_db

logger = logging.getLogger("gcia.ingestion")

# Used only when no ANTHROPIC_API_KEY is configured, so the pipeline is
# runnable out of the box. This is a placeholder, not real analysis - see
# the warning logged in run(). Covers every field any Lane 1 LLM-backed
# agent might read via .get(...).
_NO_KEY_FALLBACK_RESPONSE = {
    "is_relevant": True,
    "reason": "no ANTHROPIC_API_KEY configured; placeholder pass-through",
    "confidence": 0.9,
    "overall_label": "neutral",
    "overall_score": 0.0,
    "aspect_sentiment": {},
    "intensity": 0.0,
    "emotions": {},
    "intents": [],
    "claims": [],
}


def _build_connector(connector_name: str, source_url: str):
    if connector_name == "rss":
        return RssNewsConnector(source_url)
    if connector_name == "reddit":
        return RedditPublicConnector(source_url)
    raise ValueError(f"unknown connector: {connector_name!r} (expected 'rss' or 'reddit')")


def run(
    company_id: str,
    canonical_name: str,
    source_url: str,
    connector_name: str = "rss",
    limit: int | None = None,
) -> int:
    """`limit` caps how many raw items from the connector are processed -
    mainly a cost/time control: with a real LLM provider, each item costs
    several model calls (relevance, sentiment, emotion, intent, claim), so
    an unbounded feed (Google News RSS can return 100 items) can take a long
    time on a slow provider (e.g. local Ollama on CPU). None means no cap.
    """
    init_db()
    provider = resolve_provider(_NO_KEY_FALLBACK_RESPONSE)

    context = RunContext(
        tenant_id="local",
        budget=Budget(
            max_tokens=settings.gcia_max_tokens_per_run,
            max_cost_usd=settings.gcia_max_cost_usd_per_run,
        ),
        model_gateway=ModelGateway(provider=provider),
    )
    company = Company(company_id=company_id, canonical_name=canonical_name)

    normalization = NormalizationAgent()
    language = LanguageAgent()
    geography = GeographyAgent()
    verification = VerificationAgent()
    relevance = RelevanceAgent()
    sentiment = SentimentAgent()
    emotion = EmotionAgent()
    intent = IntentAgent()
    claim = ClaimAgent()

    session = SessionLocal()
    try:
        repository.upsert_company(session, company)

        connector = _build_connector(connector_name, source_url)
        ingested = 0
        for item_number, raw in enumerate(connector.collect(), start=1):
            if limit is not None and item_number > limit:
                break
            discussion = normalization.run(raw, context)

            # Cheap, deterministic Lane 1 steps (NONE tier) run on every item
            # regardless of relevance - they inform storage, not cost.
            discussion.language = language.run(discussion, context)
            country, country_confidence = geography.run(discussion, context)
            discussion.country = country
            discussion.country_confidence = country_confidence
            if discussion.original_url:
                discussion.url_status = verification.run(discussion.original_url, context)

            repository.upsert_discussion(session, company.company_id, discussion)

            relevance_result = relevance.run((discussion, company), context)
            repository.save_relevance(session, relevance_result)
            if not relevance_result.is_relevant:
                continue

            sentiment_result = sentiment.run(discussion, context)
            repository.save_sentiment(session, sentiment_result)

            emotion_result = emotion.run(discussion, context)
            intent_result = intent.run(discussion, context)
            claims = claim.run(discussion, context)
            for extracted_claim in claims:
                # claim_id as built by ClaimAgent is scoped only to
                # discussion_id, which is not unique across companies (two
                # companies can validly ingest identical content) - rescope
                # it here, at the point where company context is known.
                extracted_claim.claim_id = f"{company.company_id}:{extracted_claim.claim_id}"
                repository.save_claim(session, company.company_id, extracted_claim)

            evidence = Evidence(
                evidence_id=f"evidence:{company.company_id}:{discussion.discussion_id}",
                source_record_id=discussion.discussion_id,
                original_url=discussion.original_url,
                platform=discussion.platform,
                observed_at=discussion.published_at,
                claim_supported=f"Sentiment: {sentiment_result.overall_label}",
                excerpt=discussion.content[:280],
                language=discussion.language,
                country=discussion.country,
                relevance=relevance_result.confidence,
                evidence_confidence=sentiment_result.confidence,
                created_at=datetime.now(timezone.utc),
            )
            repository.save_evidence(
                session,
                company.company_id,
                evidence,
                analytical_labels={
                    "emotions": emotion_result.emotions,
                    "intents": intent_result.intents,
                    "claim_count": len(claims),
                    "url_status": discussion.url_status,
                },
            )
            ingested += 1
    finally:
        session.close()

    logger.info("ingested %d relevant discussions for %s", ingested, company_id)
    return ingested


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--company-id", required=True)
    parser.add_argument("--company-name", required=True)
    parser.add_argument("--feed-url", required=True, help="RSS feed URL or Reddit listing URL")
    parser.add_argument("--connector", default="rss", choices=["rss", "reddit"])
    parser.add_argument(
        "--limit", type=int, default=None, help="max raw items to process (default: no cap)"
    )
    args = parser.parse_args()
    count = run(
        args.company_id,
        args.company_name,
        args.feed_url,
        connector_name=args.connector,
        limit=args.limit,
    )
    print(f"ingested {count} relevant discussions for {args.company_id}")


if __name__ == "__main__":
    main()
