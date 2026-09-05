from __future__ import annotations

from pydantic import BaseModel, Field


class Topic(BaseModel):
    topic_id: str
    company_id: str
    label: str
    discussion_ids: list[str] = Field(default_factory=list)
    volume: int = 0
    baseline_volume: int = 0
    growth_rate: float | None = None
    is_emerging: bool = False
    confidence: float
    agent_version: str
