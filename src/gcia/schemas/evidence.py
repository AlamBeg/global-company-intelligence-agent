from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class Evidence(BaseModel):
    evidence_id: str
    source_record_id: str
    original_url: str | None
    platform: str
    observed_at: datetime | None
    claim_supported: str
    excerpt: str
    language: str | None
    country: str | None
    relevance: float
    analytical_labels: dict[str, str] = Field(default_factory=dict)
    evidence_confidence: float
    model_versions: dict[str, str] = Field(default_factory=dict)
    created_at: datetime
