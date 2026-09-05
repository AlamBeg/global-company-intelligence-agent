from __future__ import annotations

from gcia.common.agent import Agent, ModelTier
from gcia.common.context import RunContext
from gcia.schemas.company import Company

_SYSTEM = (
    "You expand search vocabulary for finding public discussion about a "
    "company: aliases, local-language names, transliterations, common "
    'misspellings, hashtags, and product terminology. Respond with JSON: '
    '{"queries": list}.'
)


class DiscoveryAgent(Agent[Company, list[str]]):
    """Only invoked on demand (Lane 3) when existing coverage for a query is
    thin - not run continuously, which keeps it cheap despite using the
    reasoning-heavy tier."""

    name = "discovery"
    version = "1.0"
    tier = ModelTier.LARGE

    def run(self, input: Company, context: RunContext) -> list[str]:
        prompt = (
            f"Company: {input.canonical_name}\n"
            f"Known aliases: {[a.alias for a in input.aliases]}\n"
            f"Known tickers: {input.tickers}"
        )
        result = context.model_gateway.complete(
            tier=ModelTier.LARGE,
            system=_SYSTEM,
            prompt=prompt,
            schema_hint='{"queries": list}',
            context=context,
        )
        return list(result.output.get("queries", []))
