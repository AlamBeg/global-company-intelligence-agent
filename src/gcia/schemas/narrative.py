from __future__ import annotations

from pydantic import BaseModel, Field


class DuplicateCluster(BaseModel):
    cluster_id: str
    canonical_discussion_id: str
    member_discussion_ids: list[str] = Field(default_factory=list)
    derivative_type: str  # repost, syndication, quote, translation, copy, update
    similarity_score: float
    confidence: float


class Narrative(BaseModel):
    narrative_id: str
    company_id: str
    label: str
    discussion_ids: list[str] = Field(default_factory=list)
    origin_discussion_id: str | None = None
    confidence: float
    agent_version: str
