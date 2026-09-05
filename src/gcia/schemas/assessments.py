from __future__ import annotations

from pydantic import BaseModel, Field


class RelevanceAssessment(BaseModel):
    discussion_id: str
    company_id: str
    is_relevant: bool
    reason: str
    confidence: float
    agent_version: str


class SentimentAssessment(BaseModel):
    discussion_id: str
    overall_label: str  # strongly_negative .. strongly_positive
    overall_score: float  # -1.0 .. 1.0
    aspect_sentiment: dict[str, float] = Field(default_factory=dict)
    confidence: float
    intensity: float
    agent_version: str


class EmotionAssessment(BaseModel):
    discussion_id: str
    emotions: dict[str, float] = Field(default_factory=dict)  # e.g. {"anger": 0.7}
    confidence: float
    agent_version: str


class IntentAssessment(BaseModel):
    discussion_id: str
    intents: list[str] = Field(default_factory=list)  # purchase, churn, complaint, ...
    confidence: float
    agent_version: str


class Claim(BaseModel):
    claim_id: str
    discussion_id: str
    claim_type: str  # observed_experience, reported_statement, allegation, inferred_pattern
    text: str
    confidence: float
    agent_version: str
