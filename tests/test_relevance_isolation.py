from __future__ import annotations

from datetime import datetime, timezone

from gcia.schemas.assessments import RelevanceAssessment, SentimentAssessment
from gcia.schemas.company import Company
from gcia.schemas.discussion import Discussion
from gcia.storage import repository
from gcia.storage.db import SessionLocal, init_db


def test_relevance_judgment_does_not_leak_across_companies():
    """Two companies ingesting identical content get the same discussion_id
    (it's a content hash). RelevanceRecord's primary key is
    (discussion_id, company_id) specifically so each company can have its
    own independent judgment - this was broken by a join that matched on
    discussion_id alone, letting company B's "relevant" leak into company A's
    Lane 2 input even though company A's own judgment was "not relevant".
    """
    init_db()
    session = SessionLocal()
    try:
        shared_discussion = Discussion(
            discussion_id="shared-content-hash",
            source_id="rss",
            original_url="https://example.com/shared-article",
            platform="rss",
            source_type="news",
            collected_at="2026-01-01T00:00:00Z",
            content="An article that happens to be ingested by two different companies.",
            raw_record_id="rss:shared",
            content_hash="shared-content-hash",
        )

        repository.upsert_company(session, Company(company_id="company-a", canonical_name="Company A"))
        repository.upsert_company(session, Company(company_id="company-b", canonical_name="Company B"))
        repository.upsert_discussion(session, "company-a", shared_discussion)
        repository.upsert_discussion(session, "company-b", shared_discussion)

        # Company A judges it irrelevant; Company B judges the identical
        # content relevant. Each company's own judgment must be respected.
        repository.save_relevance(
            session,
            RelevanceAssessment(
                discussion_id="shared-content-hash",
                company_id="company-a",
                is_relevant=False,
                reason="not about company A",
                confidence=0.9,
                agent_version="1.0",
            ),
        )
        repository.save_relevance(
            session,
            RelevanceAssessment(
                discussion_id="shared-content-hash",
                company_id="company-b",
                is_relevant=True,
                reason="about company B",
                confidence=0.9,
                agent_version="1.0",
            ),
        )

        company_a_relevant = repository.list_relevant_discussions(session, "company-a")
        company_b_relevant = repository.list_relevant_discussions(session, "company-b")

        assert company_a_relevant == []
        assert len(company_b_relevant) == 1
        assert company_b_relevant[0].discussion_id == "shared-content-hash"
    finally:
        session.close()


def test_irrelevant_discussion_sentiment_excluded_from_company_summary():
    """SentimentRecord is deliberately shared across companies by content
    hash (sentiment is a property of the text, not the company - see
    models.py). But an irrelevant discussion's sentiment must not move a
    company's headline sentiment score just because the same content
    happens to have a SentimentRecord from some other company's ingestion.
    """
    init_db()
    session = SessionLocal()
    try:
        irrelevant_discussion = Discussion(
            discussion_id="off-topic-hash",
            source_id="rss",
            original_url="https://example.com/off-topic",
            platform="rss",
            source_type="news",
            collected_at=datetime.now(timezone.utc),
            content="Completely unrelated weather report.",
            raw_record_id="rss:off-topic",
            content_hash="off-topic-hash",
        )
        relevant_discussion = Discussion(
            discussion_id="on-topic-hash",
            source_id="rss",
            original_url="https://example.com/on-topic",
            platform="rss",
            source_type="news",
            collected_at=datetime.now(timezone.utc),
            content="Company C had a great quarter.",
            raw_record_id="rss:on-topic",
            content_hash="on-topic-hash",
        )

        repository.upsert_company(session, Company(company_id="company-c", canonical_name="Company C"))
        repository.upsert_discussion(session, "company-c", irrelevant_discussion)
        repository.upsert_discussion(session, "company-c", relevant_discussion)

        repository.save_relevance(
            session,
            RelevanceAssessment(
                discussion_id="off-topic-hash",
                company_id="company-c",
                is_relevant=False,
                reason="not about company C",
                confidence=0.9,
                agent_version="1.0",
            ),
        )
        repository.save_relevance(
            session,
            RelevanceAssessment(
                discussion_id="on-topic-hash",
                company_id="company-c",
                is_relevant=True,
                reason="about company C",
                confidence=0.9,
                agent_version="1.0",
            ),
        )
        # The irrelevant discussion still has a real sentiment row (e.g. left
        # over from some other company's ingestion of the identical text) -
        # very negative, which would visibly skew the aggregate if counted.
        repository.save_sentiment(
            session,
            SentimentAssessment(
                discussion_id="off-topic-hash",
                overall_label="strongly_negative",
                overall_score=-1.0,
                confidence=0.9,
                intensity=0.9,
                agent_version="1.0",
            ),
        )
        repository.save_sentiment(
            session,
            SentimentAssessment(
                discussion_id="on-topic-hash",
                overall_label="positive",
                overall_score=0.8,
                confidence=0.9,
                intensity=0.8,
                agent_version="1.0",
            ),
        )

        summary = repository.get_company_summary(session, "company-c")

        assert summary["sentiment"]["sample_size"] == 1
        assert summary["sentiment"]["overall_score"] == 0.8
    finally:
        session.close()
