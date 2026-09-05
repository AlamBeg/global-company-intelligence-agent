from __future__ import annotations

from gcia.common.agent import Agent, ModelTier
from gcia.common.context import RunContext
from gcia.schemas.discussion import Discussion
from gcia.schemas.risk import Risk

_SYSTEM = (
    "You identify company risk signals (reputation, product, customer, "
    "employee, regulatory, security, competitive, financial, supply) from a "
    "set of discussions. You never assert that an allegation is true. "
    'Respond with JSON: {"category": str, "summary": str, "severity": float, '
    '"momentum": float, "affected_segments": list, "confidence": float}.'
)


class RiskAgent(Agent[list[Discussion], Risk]):
    """Runs per company/window over already-clustered, already-scored
    discussions (Lane 2) - low volume relative to raw items, so the LARGE
    tier is affordable here even though it is not affordable per item."""

    name = "risk"
    version = "1.0"
    tier = ModelTier.LARGE

    def run(self, input: list[Discussion], context: RunContext) -> Risk:
        sample = "\n---\n".join(d.content[:500] for d in input[:15])
        result = context.model_gateway.complete(
            tier=ModelTier.LARGE,
            system=_SYSTEM,
            prompt=sample,
            schema_hint=(
                '{"category": str, "summary": str, "severity": float, '
                '"momentum": float, "affected_segments": list, "confidence": float}'
            ),
            context=context,
        )
        return Risk(
            risk_id=f"risk:{input[0].discussion_id}",
            company_id="",
            category=str(result.output.get("category", "reputation")),
            summary=str(result.output.get("summary", "")),
            severity=float(result.output.get("severity", 0.0)),
            momentum=float(result.output.get("momentum", 0.0)),
            affected_segments=list(result.output.get("affected_segments", [])),
            evidence_ids=[d.discussion_id for d in input],
            confidence=float(result.output.get("confidence", 0.0)),
            agent_version=self.version,
        )
