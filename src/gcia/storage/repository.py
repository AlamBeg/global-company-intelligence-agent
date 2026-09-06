"""Persistence functions used by the ingestion pipeline and the API.

Writes here are idempotent by primary key (discussion_id, evidence_id,
claim_id, ...) per NFR-006 - re-running ingestion over the same feed never
creates duplicate rows.
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from gcia.schemas.assessments import Claim, RelevanceAssessment, SentimentAssessment
from gcia.schemas.company import Company
from gcia.schemas.discussion import Discussion
from gcia.schemas.evidence import Evidence
from gcia.schemas.narrative import DuplicateCluster, Narrative
from gcia.schemas.risk import Risk
from gcia.schemas.topic import Topic
from gcia.storage.models import (
    ClaimRecord,
    CompanyRecord,
    DiscussionRecord,
    DuplicateClusterRecord,
    EvidenceRecord,
    NarrativeRecord,
    RelevanceRecord,
    RiskRecord,
    SentimentRecord,
    TopicRecord,
)


def upsert_company(session: Session, company: Company) -> None:
    existing = session.get(CompanyRecord, company.company_id)
    if existing:
        existing.canonical_name = company.canonical_name
    else:
        session.add(
            CompanyRecord(
                company_id=company.company_id,
                canonical_name=company.canonical_name,
                schema_version=company.schema_version,
            )
        )
    session.commit()


def update_company_credibility(session: Session, company_id: str, score: float) -> None:
    company = session.get(CompanyRecord, company_id)
    if company:
        company.credibility_score = score
        session.commit()


def update_company_impact(session: Session, company_id: str, score: float) -> None:
    company = session.get(CompanyRecord, company_id)
    if company:
        company.avg_impact_score = score
        session.commit()


def upsert_discussion(session: Session, company_id: str, discussion: Discussion) -> None:
    if session.get(DiscussionRecord, (discussion.discussion_id, company_id)):
        return  # idempotent per (discussion_id, company_id) - NFR-006
    session.add(
        DiscussionRecord(
            discussion_id=discussion.discussion_id,
            company_id=company_id,
            source_id=discussion.source_id,
            original_url=discussion.original_url,
            url_status=discussion.url_status,
            platform=discussion.platform,
            published_at=discussion.published_at,
            collected_at=discussion.collected_at,
            title=discussion.title,
            content=discussion.content,
            content_hash=discussion.content_hash,
            language=discussion.language,
            country=discussion.country,
            country_confidence=discussion.country_confidence,
            engagement=discussion.engagement,
        )
    )
    session.commit()


def save_relevance(session: Session, assessment: RelevanceAssessment) -> None:
    session.merge(
        RelevanceRecord(
            discussion_id=assessment.discussion_id,
            company_id=assessment.company_id,
            is_relevant=assessment.is_relevant,
            reason=assessment.reason,
            confidence=assessment.confidence,
            agent_version=assessment.agent_version,
        )
    )
    session.commit()


def save_sentiment(session: Session, assessment: SentimentAssessment) -> None:
    session.merge(
        SentimentRecord(
            discussion_id=assessment.discussion_id,
            overall_label=assessment.overall_label,
            overall_score=assessment.overall_score,
            confidence=assessment.confidence,
            agent_version=assessment.agent_version,
        )
    )
    session.commit()


def save_claim(session: Session, company_id: str, claim: Claim) -> None:
    session.merge(
        ClaimRecord(
            claim_id=claim.claim_id,
            discussion_id=claim.discussion_id,
            company_id=company_id,
            claim_type=claim.claim_type,
            text=claim.text,
            confidence=claim.confidence,
            agent_version=claim.agent_version,
        )
    )
    session.commit()


def save_evidence(
    session: Session,
    company_id: str,
    evidence: Evidence,
    analytical_labels: dict | None = None,
) -> None:
    session.merge(
        EvidenceRecord(
            evidence_id=evidence.evidence_id,
            discussion_id=evidence.source_record_id,
            company_id=company_id,
            platform=evidence.platform,
            original_url=evidence.original_url,
            excerpt=evidence.excerpt,
            claim_supported=evidence.claim_supported,
            evidence_confidence=evidence.evidence_confidence,
            analytical_labels=analytical_labels or {},
            created_at=evidence.created_at,
        )
    )
    session.commit()


def list_relevant_discussions(session: Session, company_id: str) -> list[Discussion]:
    """Lane 2 input: only discussions Lane 1's RelevanceAgent marked relevant
    (FR-008) - irrelevant items are excluded from company-level clustering,
    topics, and risk."""
    rows = (
        session.query(DiscussionRecord)
        .join(RelevanceRecord, RelevanceRecord.discussion_id == DiscussionRecord.discussion_id)
        .filter(DiscussionRecord.company_id == company_id, RelevanceRecord.is_relevant.is_(True))
        .all()
    )
    return [_to_discussion_schema(r) for r in rows]


def _to_discussion_schema(r: DiscussionRecord) -> Discussion:
    return Discussion(
        discussion_id=r.discussion_id,
        source_id=r.source_id,
        original_url=r.original_url,
        url_status=r.url_status,
        platform=r.platform,
        source_type="unknown",
        published_at=r.published_at,
        collected_at=r.collected_at,
        title=r.title,
        content=r.content,
        raw_record_id=r.discussion_id,
        content_hash=r.content_hash,
        language=r.language,
        country=r.country,
        country_confidence=r.country_confidence,
        engagement=r.engagement or {},
    )


def clear_lane2_outputs(session: Session, company_id: str) -> None:
    """Lane 2 is idempotent per (company, window) at the *set* level, not per
    row like Lane 1: re-running a window replaces prior derived
    clusters/topics/risk/narratives rather than accumulating duplicates
    alongside them.
    """
    session.query(TopicRecord).filter(TopicRecord.company_id == company_id).delete()
    session.query(NarrativeRecord).filter(NarrativeRecord.company_id == company_id).delete()
    session.query(RiskRecord).filter(RiskRecord.company_id == company_id).delete()
    session.query(DuplicateClusterRecord).filter(
        DuplicateClusterRecord.company_id == company_id
    ).delete()
    session.commit()


def save_duplicate_cluster(session: Session, company_id: str, cluster: DuplicateCluster) -> None:
    session.merge(
        DuplicateClusterRecord(
            cluster_id=cluster.cluster_id,
            company_id=company_id,
            canonical_discussion_id=cluster.canonical_discussion_id,
            member_discussion_ids=cluster.member_discussion_ids,
            derivative_type=cluster.derivative_type,
            similarity_score=cluster.similarity_score,
            confidence=cluster.confidence,
        )
    )
    session.commit()


def save_topic(session: Session, company_id: str, topic: Topic) -> None:
    session.merge(
        TopicRecord(
            topic_id=topic.topic_id,
            company_id=company_id,
            label=topic.label,
            volume=topic.volume,
            confidence=topic.confidence,
            agent_version=topic.agent_version,
            discussion_ids=topic.discussion_ids,
        )
    )
    session.commit()


def save_narrative(session: Session, company_id: str, narrative: Narrative) -> None:
    session.merge(
        NarrativeRecord(
            narrative_id=narrative.narrative_id,
            company_id=company_id,
            label=narrative.label,
            discussion_ids=narrative.discussion_ids,
            origin_discussion_id=narrative.origin_discussion_id,
            confidence=narrative.confidence,
            agent_version=narrative.agent_version,
        )
    )
    session.commit()


def save_risk(session: Session, company_id: str, risk: Risk) -> None:
    session.merge(
        RiskRecord(
            risk_id=risk.risk_id,
            company_id=company_id,
            category=risk.category,
            summary=risk.summary,
            severity=risk.severity,
            momentum=risk.momentum,
            confidence=risk.confidence,
            agent_version=risk.agent_version,
            affected_segments=risk.affected_segments,
        )
    )
    session.commit()


def get_company_summaries(session: Session, company_ids: list[str]) -> dict[str, dict]:
    """Batch form of get_company_summary for comparison (FR-031) - each
    company is scored through the exact same pipeline/query, so results are
    directly comparable rather than computed with different assumptions."""
    return {
        company_id: summary
        for company_id in company_ids
        if (summary := get_company_summary(session, company_id)) is not None
    }


def get_company_summary(session: Session, company_id: str) -> dict | None:
    company = session.get(CompanyRecord, company_id)
    if not company:
        return None

    discussions = (
        session.query(DiscussionRecord).filter(DiscussionRecord.company_id == company_id).all()
    )
    sentiments = (
        session.query(SentimentRecord)
        .join(DiscussionRecord, DiscussionRecord.discussion_id == SentimentRecord.discussion_id)
        .filter(DiscussionRecord.company_id == company_id)
        .all()
    )
    evidence = session.query(EvidenceRecord).filter(EvidenceRecord.company_id == company_id).all()
    claims = session.query(ClaimRecord).filter(ClaimRecord.company_id == company_id).all()
    topics = (
        session.query(TopicRecord)
        .filter(TopicRecord.company_id == company_id)
        .order_by(TopicRecord.volume.desc())
        .all()
    )
    narratives = session.query(NarrativeRecord).filter(NarrativeRecord.company_id == company_id).all()
    risks = session.query(RiskRecord).filter(RiskRecord.company_id == company_id).all()
    duplicate_clusters = (
        session.query(DuplicateClusterRecord)
        .filter(DuplicateClusterRecord.company_id == company_id)
        .all()
    )

    positive = sum(1 for s in sentiments if s.overall_score > 0.1)
    negative = sum(1 for s in sentiments if s.overall_score < -0.1)
    neutral = len(sentiments) - positive - negative
    avg_score = sum(s.overall_score for s in sentiments) / len(sentiments) if sentiments else None

    geography: dict[str, int] = {}
    for d in discussions:
        if d.country:
            geography[d.country] = geography.get(d.country, 0) + 1

    return {
        "company_id": company.company_id,
        "canonical_name": company.canonical_name,
        "discussion_count": len(discussions),
        "credibility_score": company.credibility_score,
        "avg_impact_score": company.avg_impact_score,
        "sentiment": {
            "overall_score": avg_score,
            "positive": positive,
            "neutral": neutral,
            "negative": negative,
            "sample_size": len(sentiments),
        },
        "geography": geography,
        "claim_count": len(claims),
        "evidence": [
            {
                "evidence_id": e.evidence_id,
                "original_url": e.original_url,
                "excerpt": e.excerpt,
                "claim_supported": e.claim_supported,
                "confidence": e.evidence_confidence,
                "analytical_labels": e.analytical_labels or {},
            }
            for e in evidence
        ],
        "topics": [
            {"topic_id": t.topic_id, "label": t.label, "volume": t.volume, "confidence": t.confidence}
            for t in topics
        ],
        "narratives": [
            {
                "narrative_id": n.narrative_id,
                "label": n.label,
                "size": len(n.discussion_ids),
                "confidence": n.confidence,
            }
            for n in narratives
        ],
        "risks": [
            {
                "risk_id": r.risk_id,
                "category": r.category,
                "summary": r.summary,
                "severity": r.severity,
                "momentum": r.momentum,
                "confidence": r.confidence,
            }
            for r in risks
        ],
        "narrative_dedup": {
            "duplicate_clusters": len(duplicate_clusters),
            "duplicate_discussions_grouped": sum(
                len(c.member_discussion_ids) for c in duplicate_clusters
            ),
        },
    }
