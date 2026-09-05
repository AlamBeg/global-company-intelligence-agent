from __future__ import annotations

from dataclasses import dataclass

from gcia.common.agent import Agent, ModelTier
from gcia.common.context import RunContext


@dataclass
class WindowStats:
    volume: int
    positive_pct: float
    negative_pct: float
    avg_impact: float


@dataclass
class TrendResult:
    volume_change_pct: float
    sentiment_shift: float
    impact_change_pct: float


class TrendAgent(Agent[tuple[WindowStats, WindowStats], TrendResult]):
    """Compares two already-scored windows. Deterministic arithmetic - the
    LLM-backed explanation of *why* a trend moved belongs to the Synthesis
    agent (Lane 3), which can cite evidence; this agent only detects that a
    change occurred (FR-020)."""

    name = "trend"
    version = "1.0"
    tier = ModelTier.NONE

    def run(self, input: tuple[WindowStats, WindowStats], context: RunContext) -> TrendResult:
        baseline, current = input
        volume_change = (
            ((current.volume - baseline.volume) / baseline.volume) * 100 if baseline.volume else 0.0
        )
        sentiment_shift = (current.positive_pct - current.negative_pct) - (
            baseline.positive_pct - baseline.negative_pct
        )
        impact_change = (
            ((current.avg_impact - baseline.avg_impact) / baseline.avg_impact) * 100
            if baseline.avg_impact
            else 0.0
        )
        return TrendResult(
            volume_change_pct=volume_change,
            sentiment_shift=sentiment_shift,
            impact_change_pct=impact_change,
        )
