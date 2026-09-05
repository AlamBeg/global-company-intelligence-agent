from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from gcia.agents.lane3.synthesis import SynthesisAgent
from gcia.common.auth import require_role
from gcia.common.config import settings
from gcia.common.context import Budget, RunContext
from gcia.common.model_gateway import AnthropicProvider, ModelGateway, MockProvider
from gcia.schemas.evidence import Evidence
from gcia.storage.db import SessionLocal, init_db
from gcia.storage.models import EvidenceRecord

router = APIRouter(prefix="/v1/companies", tags=["ask"])

_NO_KEY_RESPONSE = {
    "answer": "ANTHROPIC_API_KEY is not configured - this is a placeholder, not a real answer.",
    "citations": [],
    "confidence": 0.0,
}


class AskRequest(BaseModel):
    question: str


@router.post("/{company_id}/ask")
def ask_company_question(
    company_id: str, body: AskRequest, role: str = Depends(require_role("analyst"))
) -> dict:
    """FR-022 evidence-backed synthesis - the 'AI Analyst' capability.
    Answers are grounded only in evidence already ingested for this company;
    SynthesisAgent is instructed to say so explicitly rather than
    extrapolate when evidence is thin (docs/PRODUCT_REQUIREMENTS.md
    "Insufficient-evidence policy"). Requires 'analyst' role or above
    (NFR-011) since it consumes model budget per call.
    """
    init_db()
    session = SessionLocal()
    try:
        records = (
            session.query(EvidenceRecord).filter(EvidenceRecord.company_id == company_id).all()
        )
    finally:
        session.close()

    if not records:
        raise HTTPException(
            status_code=404, detail="no evidence for this company - run ingestion first"
        )

    evidence = [
        Evidence(
            evidence_id=r.evidence_id,
            source_record_id=r.discussion_id,
            original_url=r.original_url,
            platform=r.platform,
            observed_at=None,
            claim_supported=r.claim_supported,
            excerpt=r.excerpt,
            language=None,
            country=None,
            relevance=1.0,
            evidence_confidence=r.evidence_confidence,
            created_at=r.created_at,
        )
        for r in records
    ]

    provider = AnthropicProvider() if settings.anthropic_api_key else MockProvider(
        fixed_response=_NO_KEY_RESPONSE
    )
    context = RunContext(
        tenant_id="api",
        budget=Budget(
            max_tokens=settings.gcia_max_tokens_per_run,
            max_cost_usd=settings.gcia_max_cost_usd_per_run,
        ),
        model_gateway=ModelGateway(provider=provider),
    )
    result = SynthesisAgent().run((body.question, evidence), context)
    return {"answer": result.answer, "citations": result.citations, "confidence": result.confidence}
