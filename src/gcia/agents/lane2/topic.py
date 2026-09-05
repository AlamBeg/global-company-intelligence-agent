from __future__ import annotations

from gcia.common.agent import Agent, ModelTier
from gcia.common.context import RunContext
from gcia.schemas.discussion import Discussion
from gcia.schemas.topic import Topic

_SYSTEM = (
    "You label the dominant topic of a cluster of related discussions in a "
    'few words. Respond with JSON: {"label": str, "confidence": float}.'
)


class TopicAgent(Agent[list[Discussion], Topic]):
    """Runs once per candidate cluster (already grouped upstream by embedding
    similarity), not once per discussion - clusters are orders of magnitude
    fewer than raw items, which is what makes the LARGE tier affordable here.
    """

    name = "topic"
    version = "1.0"
    tier = ModelTier.LARGE

    def run(self, input: list[Discussion], context: RunContext) -> Topic:
        sample = "\n---\n".join(d.content[:500] for d in input[:10])
        result = context.model_gateway.complete(
            tier=ModelTier.LARGE,
            system=_SYSTEM,
            prompt=sample,
            schema_hint='{"label": str, "confidence": float}',
            context=context,
        )
        return Topic(
            topic_id=f"topic:{input[0].discussion_id}",
            company_id="",
            label=str(result.output.get("label", "unlabeled")),
            discussion_ids=[d.discussion_id for d in input],
            volume=len(input),
            confidence=float(result.output.get("confidence", 0.0)),
            agent_version=self.version,
        )
