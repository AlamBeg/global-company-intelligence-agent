from __future__ import annotations

from dataclasses import dataclass

from gcia.common.agent import Agent, ModelTier
from gcia.common.context import RunContext
from gcia.schemas.evidence import Evidence

_SYSTEM = (
    "You answer a question about a company using only the provided evidence "
    "records. Every material statement must cite the evidence_id(s) that "
    "support it. If the evidence is insufficient, say so explicitly instead "
    'of extrapolating. Respond with JSON: {"answer": str, "citations": list, '
    '"confidence": float}.'
)


@dataclass
class SynthesisResult:
    answer: str
    citations: list[str]
    confidence: float


class SynthesisAgent(Agent[tuple[str, list[Evidence]], SynthesisResult]):
    """Lane 3, on demand. Retrieval over already-computed evidence and
    assessments - it never recomputes sentiment/impact/risk itself, and it
    must not answer past what the retrieved evidence actually supports
    (docs/PRODUCT_REQUIREMENTS.md "Insufficient-evidence policy")."""

    name = "synthesis"
    version = "1.0"
    tier = ModelTier.LARGE

    def run(self, input: tuple[str, list[Evidence]], context: RunContext) -> SynthesisResult:
        question, evidence = input
        evidence_block = "\n".join(
            f"[{e.evidence_id}] {e.excerpt} (source: {e.original_url})" for e in evidence
        )
        prompt = f"Question: {question}\n\nEvidence:\n{evidence_block}"
        result = context.model_gateway.complete(
            tier=ModelTier.LARGE,
            system=_SYSTEM,
            prompt=prompt,
            schema_hint='{"answer": str, "citations": list, "confidence": float}',
            context=context,
        )
        return SynthesisResult(
            answer=str(result.output.get("answer", "")),
            citations=list(result.output.get("citations", [])),
            confidence=float(result.output.get("confidence", 0.0)),
        )
