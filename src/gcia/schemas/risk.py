from __future__ import annotations

from pydantic import BaseModel, Field


class Risk(BaseModel):
    risk_id: str
    company_id: str
    category: str  # reputation, product, customer, employee, regulatory, security, competitive, financial, supply
    summary: str
    severity: float
    momentum: float
    affected_segments: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    confidence: float
    agent_version: str
