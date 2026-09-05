from __future__ import annotations

import urllib.request

from gcia.common.agent import Agent, ModelTier
from gcia.common.context import RunContext


class VerificationAgent(Agent[str, str]):
    """Checks URL accessibility before an insight is shown, returning one of
    the verification states from docs/EVIDENCE_AND_PROVENANCE.md. Never
    generates or repairs a URL - only reports what it observed."""

    name = "verification"
    version = "1.0"
    tier = ModelTier.NONE

    def run(self, input: str, context: RunContext) -> str:
        try:
            request = urllib.request.Request(input, method="HEAD")
            with urllib.request.urlopen(request, timeout=5) as response:
                if response.status < 400:
                    return "verified"
                return "inaccessible"
        except Exception:
            return "inaccessible"
