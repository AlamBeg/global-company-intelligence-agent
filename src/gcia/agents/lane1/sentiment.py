from __future__ import annotations

from gcia.common.agent import Agent, ModelTier
from gcia.common.coercion import coerce_float_dict
from gcia.common.context import RunContext
from gcia.common.model_gateway import prompt_cache_key
from gcia.schemas.assessments import SentimentAssessment
from gcia.schemas.discussion import Discussion

_SYSTEM = (
    "You score sentiment expressed in text toward the subject only - never "
    "adjust for how popular, viral, or credible the post is. Respond with "
    'JSON: {"overall_label": str, "overall_score": float (-1.0 to 1.0), '
    '"aspect_sentiment": {"<aspect>": <number -1.0 to 1.0>, ...} (numbers '
    'only, never words like "positive"), "confidence": float (0.0 to 1.0), '
    '"intensity": float (0.0 to 1.0)}.'
)


class SentimentAgent(Agent[Discussion, SentimentAssessment]):
    """Deliberately never receives engagement/reach/credibility fields as
    input - that separation is what keeps sentiment independent of impact
    (docs/AI_SCORING_MODEL.md "Design rule").
    """

    name = "sentiment"
    version = "1.0"
    tier = ModelTier.SMALL

    def run(self, input: Discussion, context: RunContext) -> SentimentAssessment:
        result = context.model_gateway.complete(
            tier=ModelTier.SMALL,
            system=_SYSTEM,
            prompt=f"Text: {input.content[:2000]}",
            schema_hint=(
                '{"overall_label": str, "overall_score": float, '
                '"aspect_sentiment": {"<aspect>": <float -1.0 to 1.0>}, '
                '"confidence": float, "intensity": float}'
            ),
            context=context,
            cache_key=prompt_cache_key(self.agent_id, input.content_hash),
        )
        return SentimentAssessment(
            discussion_id=input.discussion_id,
            overall_label=str(result.output.get("overall_label", "neutral")),
            overall_score=float(result.output.get("overall_score", 0.0)),
            aspect_sentiment=coerce_float_dict(result.output.get("aspect_sentiment", {})),
            confidence=float(result.output.get("confidence", 0.0)),
            intensity=float(result.output.get("intensity", 0.0)),
            agent_version=self.version,
        )
