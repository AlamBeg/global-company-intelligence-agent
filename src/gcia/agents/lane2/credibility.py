from __future__ import annotations

from dataclasses import dataclass

from gcia.common.agent import Agent, ModelTier
from gcia.common.context import RunContext


@dataclass
class CredibilityInputs:
    source_history_score: float
    author_identity_consistency: float
    evidence_quality: float
    originality: float
    specialization: float
    engagement_authenticity: float
    corroboration: float


_WEIGHTS = {
    "source_history_score": 0.2,
    "author_identity_consistency": 0.15,
    "evidence_quality": 0.2,
    "originality": 0.1,
    "specialization": 0.1,
    "engagement_authenticity": 0.15,
    "corroboration": 0.1,
}


class CredibilityAgent(Agent[CredibilityInputs, float]):
    """Deterministic feature score - explicitly not a truth score
    (docs/AI_SCORING_MODEL.md)."""

    name = "credibility"
    version = "1.0"
    tier = ModelTier.NONE

    def run(self, input: CredibilityInputs, context: RunContext) -> float:
        return sum(getattr(input, field) * weight for field, weight in _WEIGHTS.items())
