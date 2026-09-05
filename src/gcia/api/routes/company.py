from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from gcia.common.auth import require_role
from gcia.storage import repository
from gcia.storage.db import SessionLocal, init_db

router = APIRouter(prefix="/v1/companies", tags=["company"])


@router.get("/{company_id}")
def get_company_profile(company_id: str, role: str = Depends(require_role("viewer"))) -> dict:
    """FR-026 dashboard summary, backed by whatever has been ingested via
    `python -m gcia.ingestion.run_ingestion`. Aggregated view - available to
    the 'viewer' role and above (NFR-011)."""
    init_db()
    session = SessionLocal()
    try:
        summary = repository.get_company_summary(session, company_id)
    finally:
        session.close()
    if summary is None:
        raise HTTPException(status_code=404, detail="company not found - run ingestion first")
    return summary
