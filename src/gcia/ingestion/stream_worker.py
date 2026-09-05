from __future__ import annotations

from dataclasses import dataclass

from gcia.agents.lane1.language import LanguageAgent
from gcia.agents.lane1.normalization import NormalizationAgent
from gcia.common.context import RunContext
from gcia.schemas.discussion import Discussion, RawRecord


@dataclass
class Lane1Result:
    discussion: Discussion
    language: str


class Lane1StreamWorker:
    """In-process reference runner for Lane 1 (see
    MULTI_AGENT_ARCHITECTURE.md "Execution model"). Production replaces this
    with per-agent consumer groups on the event bus (Kafka/Redpanda), one
    stage per topic, so each agent scales and fails independently. This
    runner exists so the agent contracts can be exercised locally without
    standing up a broker.
    """

    def __init__(self) -> None:
        self.normalization = NormalizationAgent()
        self.language = LanguageAgent()
        # Relevance/Sentiment/Emotion/Intent/Claim/Geography plug in the same
        # way once a Company + a live model gateway (API key) are available.

    def process(self, raw: RawRecord, context: RunContext) -> Lane1Result:
        discussion = self.normalization.run(raw, context)
        language = self.language.run(discussion, context)
        return Lane1Result(discussion=discussion, language=language)
