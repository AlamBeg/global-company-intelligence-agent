from __future__ import annotations

from fastapi import APIRouter, Depends

from gcia.common.auth import require_role
from gcia.workflows.run_trend import run as run_trend

router = APIRouter(prefix="/v1/companies", tags=["trend"])


@router.get("/{company_id}/trend")
def get_trend(
    company_id: str, window_days: int = 7, role: str = Depends(require_role("viewer"))
) -> dict:
    """FR-020 trend analysis: compares two adjacent windows of `window_days`
    length using real `collected_at` timestamps. A dataset ingested in one
    burst has no real time spread, so ~0% change is the honest answer, not a
    bug - see run_trend.py's module docstring.
    """
    return run_trend(company_id, window_days=window_days)
