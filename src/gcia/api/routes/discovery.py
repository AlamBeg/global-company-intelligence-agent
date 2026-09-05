from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from gcia.agents.lane3.discovery import DiscoveryAgent
from gcia.common.auth import require_role
from gcia.common.config import settings
from gcia.common.context import Budget, RunContext
from gcia.common.model_gateway import AnthropicProvider, ModelGateway, MockProvider
from gcia.schemas.company import Company, EntityAlias

router = APIRouter(prefix="/v1/companies", tags=["discovery"])

_NO_KEY_RESPONSE = {"queries": []}


class DiscoverRequest(BaseModel):
    canonical_name: str
    known_aliases: list[str] = Field(default_factory=list)
    known_tickers: list[str] = Field(default_factory=list)


@router.post("/{company_id}/discover-queries")
def discover_queries(
    company_id: str, body: DiscoverRequest, role: str = Depends(require_role("analyst"))
) -> dict:
    """FR-003 dynamic discovery: suggests search vocabulary (aliases,
    local-language names, transliterations, misspellings, hashtags) for a
    company, to expand connector query coverage. Does not touch storage or
    run any connector itself - purely a suggestion step, run before or
    alongside `gcia.ingestion.run_ingestion`.
    """
    provider = (
        AnthropicProvider() if settings.anthropic_api_key else MockProvider(fixed_response=_NO_KEY_RESPONSE)
    )
    context = RunContext(
        tenant_id="api",
        budget=Budget(
            max_tokens=settings.gcia_max_tokens_per_run,
            max_cost_usd=settings.gcia_max_cost_usd_per_run,
        ),
        model_gateway=ModelGateway(provider=provider),
    )
    company = Company(
        company_id=company_id,
        canonical_name=body.canonical_name,
        aliases=[EntityAlias(alias=a, alias_type="local_name") for a in body.known_aliases],
        tickers=body.known_tickers,
    )
    queries = DiscoveryAgent().run(company, context)
    return {"company_id": company_id, "suggested_queries": queries}
