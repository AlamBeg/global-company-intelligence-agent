from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from gcia.common.auth import require_role
from gcia.storage.db import SessionLocal, init_db
from gcia.storage.models import EvidenceRecord

router = APIRouter(prefix="/v1/evidence", tags=["evidence"])


@router.get("/{evidence_id}")
def get_evidence(evidence_id: str, role: str = Depends(require_role("analyst"))) -> dict:
    """FR-023 / FR-025. Raw evidence detail requires 'analyst' role or above
    (NFR-011) - more sensitive than the aggregated company summary."""
    init_db()
    session = SessionLocal()
    try:
        record = session.get(EvidenceRecord, evidence_id)
    finally:
        session.close()
    if record is None:
        raise HTTPException(status_code=404, detail="evidence not found")
    return {
        "evidence_id": record.evidence_id,
        "discussion_id": record.discussion_id,
        "company_id": record.company_id,
        "original_url": record.original_url,
        "excerpt": record.excerpt,
        "claim_supported": record.claim_supported,
        "confidence": record.evidence_confidence,
    }
