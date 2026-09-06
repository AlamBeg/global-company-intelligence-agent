"""Company Entity Agent (FR-001, FR-002).

Resolves a free-text company identifier - name, ticker, domain, alias,
local-language name, or common misspelling - to a canonical Company.

This is not Lane 1/2/3: per docs/SYSTEM_ARCHITECTURE.md it belongs to the
"Entity and discovery layer" that runs once per user request, before any
collection begins.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from gcia.common.agent import Agent, ModelTier
from gcia.common.context import RunContext
from gcia.schemas.company import Company, EntityAlias

# A tiny seed registry so resolution has something real to match against.
# This is not a production entity database - production needs a real
# company knowledge base (e.g. GLEIF, OpenCorporates, or a licensed
# provider), plus a path for tenants to register their own known aliases.
_SEED_REGISTRY: list[Company] = [
    Company(
        company_id="acme-corp",
        canonical_name="Acme Corp",
        aliases=[
            EntityAlias(alias="Acme", alias_type="brand"),
            EntityAlias(alias="ACME", alias_type="brand"),
        ],
        tickers=["ACM"],
        domains=["acme.example.com"],
    ),
]


@dataclass
class EntityResolutionResult:
    company: Company
    matched_on: str  # exact_name, alias, ticker, domain, new
    confidence: float
    ambiguous_candidates: list[Company] = field(default_factory=list)


def _slugify(text: str) -> str:
    slug = "-".join(text.strip().lower().split())[:64]
    return slug or "unknown-company"


class CompanyEntityAgent(Agent[str, EntityResolutionResult]):
    """Deterministic registry lookup (tier NONE) - no LLM call needed for
    exact/alias/ticker/domain matches, which is the common case. A
    production version would query a real company database and reserve an
    LLM call for genuine disambiguation (e.g. two distinct companies sharing
    a name, resolved using surrounding context) - this seed-registry demo
    has no such collisions to disambiguate.

    Unrecognized input does not fail (FR-001 requires accepting arbitrary
    identifiers, not only pre-registered ones) - it resolves to a new
    canonical entity with reduced confidence instead.
    """

    name = "company_entity"
    version = "1.0"
    tier = ModelTier.NONE

    def run(self, input: str, context: RunContext) -> EntityResolutionResult:
        query = input.strip()
        query_lower = query.lower()

        for company in _SEED_REGISTRY:
            if query_lower in (company.company_id.lower(), company.canonical_name.lower()):
                return EntityResolutionResult(company=company, matched_on="exact_name", confidence=1.0)
            if any(a.alias.lower() == query_lower for a in company.aliases):
                return EntityResolutionResult(company=company, matched_on="alias", confidence=0.9)
            if query.upper() in company.tickers:
                return EntityResolutionResult(company=company, matched_on="ticker", confidence=0.9)
            if query_lower in (d.lower() for d in company.domains):
                return EntityResolutionResult(company=company, matched_on="domain", confidence=0.9)

        new_company = Company(company_id=_slugify(query), canonical_name=query)
        return EntityResolutionResult(company=new_company, matched_on="new", confidence=0.5)
