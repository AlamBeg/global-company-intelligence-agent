from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, DateTime, Float, ForeignKey, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class CompanyRecord(Base):
    __tablename__ = "companies"

    company_id: Mapped[str] = mapped_column(String, primary_key=True)
    canonical_name: Mapped[str] = mapped_column(String)
    schema_version: Mapped[str] = mapped_column(String, default="1.0")
    # Company-level, from CredibilityAgent over Lane 2 canonical discussions -
    # not a truth score (docs/AI_SCORING_MODEL.md).
    credibility_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    # Company-level average of ImpactAgent over Lane 2 canonical discussions.
    avg_impact_score: Mapped[float | None] = mapped_column(Float, nullable=True)


class DiscussionRecord(Base):
    """Primary key is (discussion_id, company_id), not discussion_id alone.

    discussion_id is content-derived (hash of platform + source-native id),
    so identical content ingested for two different companies would
    otherwise collide onto one row and silently get reassigned to whichever
    company wrote it last. Relevance is inherently per-company (FR-008), so
    the same content can validly appear once per company it was ingested
    for, with its own relevance/evidence/topic/risk trail.
    """

    __tablename__ = "discussions"

    discussion_id: Mapped[str] = mapped_column(String, primary_key=True)
    company_id: Mapped[str] = mapped_column(
        String, ForeignKey("companies.company_id"), primary_key=True
    )
    source_id: Mapped[str] = mapped_column(String)
    original_url: Mapped[str | None] = mapped_column(String, nullable=True)
    url_status: Mapped[str] = mapped_column(String)
    platform: Mapped[str] = mapped_column(String)
    published_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    collected_at: Mapped[datetime] = mapped_column(DateTime)
    title: Mapped[str | None] = mapped_column(String, nullable=True)
    content: Mapped[str] = mapped_column(Text)
    content_hash: Mapped[str] = mapped_column(String)
    language: Mapped[str | None] = mapped_column(String, nullable=True)
    country: Mapped[str | None] = mapped_column(String, nullable=True)
    country_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    engagement: Mapped[dict] = mapped_column(JSON, default=dict)


class RelevanceRecord(Base):
    """Primary key is (discussion_id, company_id): the same content can be
    judged relevant to one company and not another (FR-008), so relevance is
    inherently per-company, not a fact about the content alone.
    """

    __tablename__ = "relevance_assessments"

    discussion_id: Mapped[str] = mapped_column(String, primary_key=True)
    company_id: Mapped[str] = mapped_column(String, primary_key=True)
    is_relevant: Mapped[bool] = mapped_column()
    reason: Mapped[str] = mapped_column(Text)
    confidence: Mapped[float] = mapped_column(Float)
    agent_version: Mapped[str] = mapped_column(String)


class SentimentRecord(Base):
    """Keyed by discussion_id alone: sentiment is a property of the content
    itself (docs/AI_SCORING_MODEL.md), not the company evaluating it, so
    sharing one row across companies for identical content is correct, not
    a collision - unlike RelevanceRecord."""

    __tablename__ = "sentiment_assessments"

    discussion_id: Mapped[str] = mapped_column(String, primary_key=True)
    overall_label: Mapped[str] = mapped_column(String)
    overall_score: Mapped[float] = mapped_column(Float)
    confidence: Mapped[float] = mapped_column(Float)
    agent_version: Mapped[str] = mapped_column(String)


class TopicRecord(Base):
    __tablename__ = "topics"

    topic_id: Mapped[str] = mapped_column(String, primary_key=True)
    company_id: Mapped[str] = mapped_column(String)
    label: Mapped[str] = mapped_column(String)
    volume: Mapped[int] = mapped_column()
    confidence: Mapped[float] = mapped_column(Float)
    agent_version: Mapped[str] = mapped_column(String)
    discussion_ids: Mapped[list] = mapped_column(JSON, default=list)


class RiskRecord(Base):
    __tablename__ = "risks"

    risk_id: Mapped[str] = mapped_column(String, primary_key=True)
    company_id: Mapped[str] = mapped_column(String)
    category: Mapped[str] = mapped_column(String)
    summary: Mapped[str] = mapped_column(Text)
    severity: Mapped[float] = mapped_column(Float)
    momentum: Mapped[float] = mapped_column(Float)
    confidence: Mapped[float] = mapped_column(Float)
    agent_version: Mapped[str] = mapped_column(String)
    affected_segments: Mapped[list] = mapped_column(JSON, default=list)


class DuplicateClusterRecord(Base):
    __tablename__ = "duplicate_clusters"

    cluster_id: Mapped[str] = mapped_column(String, primary_key=True)
    company_id: Mapped[str] = mapped_column(String)
    canonical_discussion_id: Mapped[str] = mapped_column(String)
    member_discussion_ids: Mapped[list] = mapped_column(JSON, default=list)
    derivative_type: Mapped[str] = mapped_column(String)
    similarity_score: Mapped[float] = mapped_column(Float)
    confidence: Mapped[float] = mapped_column(Float)


class EvidenceRecord(Base):
    __tablename__ = "evidence"

    # evidence_id itself is company-scoped by construction (see
    # gcia.ingestion.run_ingestion) - discussion_id alone is not unique
    # across companies, so it is stored as a plain correlation column, not
    # an enforced foreign key.
    evidence_id: Mapped[str] = mapped_column(String, primary_key=True)
    discussion_id: Mapped[str] = mapped_column(String)
    company_id: Mapped[str] = mapped_column(String)
    platform: Mapped[str] = mapped_column(String, default="unknown")
    original_url: Mapped[str | None] = mapped_column(String, nullable=True)
    title: Mapped[str | None] = mapped_column(String, nullable=True)
    observed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    country: Mapped[str | None] = mapped_column(String, nullable=True)
    excerpt: Mapped[str] = mapped_column(Text)
    claim_supported: Mapped[str] = mapped_column(Text)
    evidence_confidence: Mapped[float] = mapped_column(Float)
    analytical_labels: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime)


class ClaimRecord(Base):
    __tablename__ = "claims"

    # claim_id is company-scoped by construction, same rationale as
    # EvidenceRecord above.
    claim_id: Mapped[str] = mapped_column(String, primary_key=True)
    discussion_id: Mapped[str] = mapped_column(String)
    company_id: Mapped[str] = mapped_column(String)
    claim_type: Mapped[str] = mapped_column(String)
    text: Mapped[str] = mapped_column(Text)
    confidence: Mapped[float] = mapped_column(Float)
    agent_version: Mapped[str] = mapped_column(String)


class NarrativeRecord(Base):
    __tablename__ = "narratives"

    narrative_id: Mapped[str] = mapped_column(String, primary_key=True)
    company_id: Mapped[str] = mapped_column(String)
    label: Mapped[str] = mapped_column(String)
    discussion_ids: Mapped[list] = mapped_column(JSON, default=list)
    origin_discussion_id: Mapped[str | None] = mapped_column(String, nullable=True)
    confidence: Mapped[float] = mapped_column(Float)
    agent_version: Mapped[str] = mapped_column(String)
