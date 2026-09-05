from __future__ import annotations

from gcia.common.agent import Agent, ModelTier
from gcia.common.context import RunContext
from gcia.schemas.discussion import Discussion
from gcia.schemas.narrative import Narrative

_SYSTEM = (
    "You summarize the shared underlying event or narrative connecting a "
    'cluster of discussions in one short label. Respond with JSON: '
    '{"label": str, "confidence": float}.'
)


class NarrativeAgent(Agent[list[Discussion], Narrative]):
    """Runs once per candidate narrative cluster (Lane 2), not per
    discussion - same cost rationale as TopicAgent."""

    name = "narrative"
    version = "1.0"
    tier = ModelTier.LARGE

    def run(self, input: list[Discussion], context: RunContext) -> Narrative:
        sample = "\n---\n".join(d.content[:500] for d in input[:10])
        result = context.model_gateway.complete(
            tier=ModelTier.LARGE,
            system=_SYSTEM,
            prompt=sample,
            schema_hint='{"label": str, "confidence": float}',
            context=context,
        )
        sorted_by_time = sorted(input, key=lambda d: d.published_at or d.collected_at)
        return Narrative(
            narrative_id=f"narrative:{input[0].discussion_id}",
            company_id="",
            label=str(result.output.get("label", "unlabeled")),
            discussion_ids=[d.discussion_id for d in input],
            origin_discussion_id=sorted_by_time[0].discussion_id,
            confidence=float(result.output.get("confidence", 0.0)),
            agent_version=self.version,
        )
