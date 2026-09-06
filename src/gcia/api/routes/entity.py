from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from gcia.agents.entity import CompanyEntityAgent
from gcia.common.auth import require_role
from gcia.common.config import settings
from gcia.common.context import Budget, RunContext
from gcia.common.model_gateway import ModelGateway, MockProvider

router = APIRouter(prefix="/v1", tags=["entity"])


class ResolveRequest(BaseModel):
    query: str


@router.post("/resolve-company")
def resolve_company(body: ResolveRequest, role: str = Depends(require_role("viewer"))) -> dict:
    """FR-001 / FR-002: resolves a free-text company identifier (name,
    alias, ticker, or domain) to a canonical entity. Deterministic registry
    lookup - no LLM call, so no ANTHROPIC_API_KEY dependency and no cost.
    """
    context = RunContext(
        tenant_id="api",
        budget=Budget(
            max_tokens=settings.gcia_max_tokens_per_run,
            max_cost_usd=settings.gcia_max_cost_usd_per_run,
        ),
        model_gateway=ModelGateway(provider=MockProvider()),  # unused: agent is tier NONE
    )
    result = CompanyEntityAgent().run(body.query, context)
    return {
        "company_id": result.company.company_id,
        "canonical_name": result.company.canonical_name,
        "matched_on": result.matched_on,
        "confidence": result.confidence,
        "is_new_entity": result.matched_on == "new",
    }
