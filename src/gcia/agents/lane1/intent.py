from __future__ import annotations

from gcia.common.agent import Agent, ModelTier
from gcia.common.context import RunContext
from gcia.common.model_gateway import prompt_cache_key
from gcia.schemas.assessments import IntentAssessment
from gcia.schemas.discussion import Discussion

_SYSTEM = (
    "You detect behavioral intent signals in text (purchase, recommendation, "
    "churn, complaint, support-seeking, advocacy, comparison, investment, "
    'hiring, boycott) only when evidence supports them. Respond with JSON: '
    '{"intents": list, "confidence": float}.'
)


class IntentAgent(Agent[Discussion, IntentAssessment]):
    name = "intent"
    version = "1.0"
    tier = ModelTier.SMALL

    def run(self, input: Discussion, context: RunContext) -> IntentAssessment:
        result = context.model_gateway.complete(
            tier=ModelTier.SMALL,
            system=_SYSTEM,
            prompt=f"Text: {input.content[:2000]}",
            schema_hint='{"intents": list, "confidence": float}',
            context=context,
            cache_key=prompt_cache_key(self.agent_id, input.content_hash),
        )
        return IntentAssessment(
            discussion_id=input.discussion_id,
            intents=list(result.output.get("intents", [])),
            confidence=float(result.output.get("confidence", 0.0)),
            agent_version=self.version,
        )
