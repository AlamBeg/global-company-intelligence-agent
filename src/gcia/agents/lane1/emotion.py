from __future__ import annotations

from gcia.common.agent import Agent, ModelTier
from gcia.common.context import RunContext
from gcia.common.model_gateway import prompt_cache_key
from gcia.schemas.assessments import EmotionAssessment
from gcia.schemas.discussion import Discussion

_SYSTEM = (
    "You detect emotions expressed in text (e.g. trust, anger, frustration, "
    "fear, excitement, disappointment, satisfaction, admiration, confusion, "
    'uncertainty). Respond with JSON: {"emotions": dict, "confidence": float}.'
)


class EmotionAgent(Agent[Discussion, EmotionAssessment]):
    name = "emotion"
    version = "1.0"
    tier = ModelTier.SMALL

    def run(self, input: Discussion, context: RunContext) -> EmotionAssessment:
        result = context.model_gateway.complete(
            tier=ModelTier.SMALL,
            system=_SYSTEM,
            prompt=f"Text: {input.content[:2000]}",
            schema_hint='{"emotions": dict, "confidence": float}',
            context=context,
            cache_key=prompt_cache_key(self.agent_id, input.content_hash),
        )
        return EmotionAssessment(
            discussion_id=input.discussion_id,
            emotions=dict(result.output.get("emotions", {})),
            confidence=float(result.output.get("confidence", 0.0)),
            agent_version=self.version,
        )
