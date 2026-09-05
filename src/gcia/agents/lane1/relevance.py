from __future__ import annotations

from gcia.common.agent import Agent, ModelTier
from gcia.common.context import RunContext
from gcia.common.model_gateway import prompt_cache_key
from gcia.schemas.assessments import RelevanceAssessment
from gcia.schemas.company import Company
from gcia.schemas.discussion import Discussion

_SYSTEM = (
    "You judge whether a piece of public discussion is materially about a "
    "named company, distinguishing it from unrelated people, places, or "
    'common-word collisions. Respond with JSON: {"is_relevant": bool, '
    '"reason": str, "confidence": float}.'
)

_ESCALATION_CONFIDENCE_THRESHOLD = 0.6


class RelevanceAgent(Agent[tuple[Discussion, Company], RelevanceAssessment]):
    """Runs on every Lane 1 item, so it defaults to the cheap tier. Only the
    ambiguous minority - where the small model itself reports low confidence -
    gets escalated to the large model. This cascade is the main cost lever
    for high-volume agents; see MULTI_AGENT_ARCHITECTURE.md "Execution model".
    """

    name = "relevance"
    version = "1.0"
    tier = ModelTier.SMALL

    def run(self, input: tuple[Discussion, Company], context: RunContext) -> RelevanceAssessment:
        discussion, company = input
        prompt = (
            f"Company: {company.canonical_name} "
            f"(aliases: {[a.alias for a in company.aliases]})\n"
            f"Content: {discussion.content[:2000]}"
        )
        schema_hint = '{"is_relevant": bool, "reason": str, "confidence": float}'
        cache_key = prompt_cache_key(self.agent_id, discussion.content_hash, company.company_id)

        result = context.model_gateway.complete(
            tier=ModelTier.SMALL,
            system=_SYSTEM,
            prompt=prompt,
            schema_hint=schema_hint,
            context=context,
            cache_key=cache_key,
        )
        confidence = float(result.output.get("confidence", 0.0))

        if confidence < _ESCALATION_CONFIDENCE_THRESHOLD:
            result = context.model_gateway.complete(
                tier=ModelTier.LARGE,
                system=_SYSTEM,
                prompt=prompt,
                schema_hint=schema_hint,
                context=context,
                cache_key=f"{cache_key}:escalated",
            )

        return RelevanceAssessment(
            discussion_id=discussion.discussion_id,
            company_id=company.company_id,
            is_relevant=bool(result.output.get("is_relevant", False)),
            reason=str(result.output.get("reason", "")),
            confidence=float(result.output.get("confidence", 0.0)),
            agent_version=self.version,
        )
