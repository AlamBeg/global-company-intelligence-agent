from __future__ import annotations

from gcia.common.agent import Agent, ModelTier
from gcia.common.context import RunContext
from gcia.common.model_gateway import prompt_cache_key
from gcia.schemas.assessments import Claim
from gcia.schemas.discussion import Discussion

_SYSTEM = (
    "You extract material factual or experiential claims from text, "
    "separating what was directly observed/reported from allegations or "
    'inferred patterns. Respond with JSON: {"claims": [{"claim_type": str, '
    '"text": str, "confidence": float}]}.'
)


class ClaimAgent(Agent[Discussion, list[Claim]]):
    name = "claim"
    version = "1.0"
    tier = ModelTier.SMALL

    def run(self, input: Discussion, context: RunContext) -> list[Claim]:
        result = context.model_gateway.complete(
            tier=ModelTier.SMALL,
            system=_SYSTEM,
            prompt=f"Text: {input.content[:2000]}",
            schema_hint='{"claims": [{"claim_type": str, "text": str, "confidence": float}]}',
            context=context,
            cache_key=prompt_cache_key(self.agent_id, input.content_hash),
        )
        claims = result.output.get("claims", [])
        return [
            Claim(
                claim_id=f"claim:{input.discussion_id}:{i}",
                discussion_id=input.discussion_id,
                claim_type=str(c.get("claim_type", "reported_statement")),
                text=str(c.get("text", "")),
                confidence=float(c.get("confidence", 0.0)),
                agent_version=self.version,
            )
            for i, c in enumerate(claims)
        ]
