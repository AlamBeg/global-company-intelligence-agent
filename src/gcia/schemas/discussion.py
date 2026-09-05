from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class RawRecord(BaseModel):
    """What a connector hands to Normalization. Connector-owned, unmodified.

    original_url is required-but-nullable rather than optional-with-omission:
    a connector must explicitly say "no stable URL exists" (None) instead of
    silently leaving it out (FR-005 / SOURCE_CONNECTORS.md "URL integrity").
    """

    platform: str
    source_native_id: str
    original_url: str | None
    author_public_name: str | None = None
    published_at: datetime | None = None
    collected_at: datetime
    title: str | None = None
    content: str
    engagement: dict[str, int] = Field(default_factory=dict)
    parent_native_id: str | None = None
    raw_payload: dict = Field(default_factory=dict)


class Discussion(BaseModel):
    discussion_id: str
    source_id: str
    original_url: str | None
    url_status: str = "unverified"  # verified, inaccessible, content_changed, deleted, paywalled, unavailable
    platform: str
    source_type: str
    author_id: str | None = None
    published_at: datetime | None = None
    collected_at: datetime
    language: str | None = None
    country: str | None = None
    country_confidence: float | None = None
    title: str | None = None
    content: str
    engagement: dict[str, int] = Field(default_factory=dict)
    parent_discussion_id: str | None = None
    raw_record_id: str
    content_hash: str
    entity_candidates: list[str] = Field(default_factory=list)
    schema_version: str = "1.0"
