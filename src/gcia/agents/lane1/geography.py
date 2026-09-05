from __future__ import annotations

from gcia.common.agent import Agent, ModelTier
from gcia.common.context import RunContext
from gcia.schemas.discussion import Discussion

# Placeholder gazetteer. Production should combine author profile locale,
# platform-provided geo tags, and a real place-name gazetteer (FR-019).
# Deliberately not an LLM call: this must run at streaming volume for free.
_COUNTRY_HINTS = {
    "usa": "US",
    "united states": "US",
    "india": "IN",
    "uk": "GB",
    "united kingdom": "GB",
}


class GeographyAgent(Agent[Discussion, tuple[str | None, float]]):
    name = "geography"
    version = "1.0"
    tier = ModelTier.NONE

    def run(self, input: Discussion, context: RunContext) -> tuple[str | None, float]:
        content_lower = input.content.lower()
        for hint, country in _COUNTRY_HINTS.items():
            if hint in content_lower:
                return country, 0.4  # low confidence: keyword match only
        return None, 0.0
