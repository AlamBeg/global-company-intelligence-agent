from __future__ import annotations

from gcia.common.agent import Agent, ModelTier
from gcia.common.context import RunContext
from gcia.schemas.discussion import Discussion

# A tiny heuristic placeholder. Production should use a dedicated language-ID
# library (e.g. fastText lid.176, or lingua) - deliberately not an LLM call:
# language detection at streaming volume must be near-free.
_LATIN_HINTS = {"the", "and", "is", "of", "to"}


class LanguageAgent(Agent[Discussion, str]):
    name = "language"
    version = "1.0"
    tier = ModelTier.NONE

    def run(self, input: Discussion, context: RunContext) -> str:
        words = set(input.content.lower().split())
        if words & _LATIN_HINTS:
            return "en"
        return "und"  # undetermined; replace with a real language-ID model
