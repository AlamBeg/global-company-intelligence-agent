from __future__ import annotations

from dataclasses import dataclass

from gcia.common.agent import Agent, ModelTier
from gcia.common.context import RunContext


@dataclass
class ImpactInputs:
    reach: float
    engagement: float
    author_influence: float
    source_credibility: float
    topic_importance: float
    velocity: float
    propagation: float
    originality: float


# Weights are illustrative starting values; must be tuned and versioned
# against evaluation data per docs/AI_SCORING_MODEL.md.
_WEIGHTS = {
    "reach": 0.15,
    "engagement": 0.15,
    "author_influence": 0.15,
    "source_credibility": 0.15,
    "topic_importance": 0.1,
    "velocity": 0.1,
    "propagation": 0.1,
    "originality": 0.1,
}
_WEIGHTS_VERSION = "1.0"


class ImpactAgent(Agent[ImpactInputs, float]):
    """Pure formula, no LLM call - impact must stay independent of a model's
    subjective read of the content (docs/AI_SCORING_MODEL.md "Design rule").
    """

    name = "impact"
    version = _WEIGHTS_VERSION
    tier = ModelTier.NONE

    def run(self, input: ImpactInputs, context: RunContext) -> float:
        return sum(getattr(input, field) * weight for field, weight in _WEIGHTS.items())
