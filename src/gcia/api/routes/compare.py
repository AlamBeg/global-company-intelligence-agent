from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from gcia.common.auth import require_role
from gcia.storage import repository
from gcia.storage.db import SessionLocal, init_db

router = APIRouter(prefix="/v1/compare", tags=["compare"])


@router.get("")
def compare_companies(company_ids: str, role: str = Depends(require_role("analyst"))) -> dict:
    """FR-031 competitive comparison. `company_ids` is a comma-separated
    list; each company is run through the identical summary computation so
    results are directly comparable, not independently eyeballed. Requires
    'analyst' role or above (NFR-011)."""
    ids = [c.strip() for c in company_ids.split(",") if c.strip()]
    if len(ids) < 2:
        raise HTTPException(status_code=400, detail="provide at least 2 comma-separated company_ids")

    init_db()
    session = SessionLocal()
    try:
        summaries = repository.get_company_summaries(session, ids)
    finally:
        session.close()

    missing = [i for i in ids if i not in summaries]
    ranked_by_sentiment = sorted(
        summaries.values(),
        key=lambda s: (s["sentiment"]["overall_score"] if s["sentiment"]["overall_score"] is not None else -999),
        reverse=True,
    )

    return {
        "companies": summaries,
        "missing_company_ids": missing,
        "ranked_by_sentiment": [c["company_id"] for c in ranked_by_sentiment],
    }
