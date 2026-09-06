from __future__ import annotations

from fastapi.testclient import TestClient

from gcia.agents.entity import CompanyEntityAgent
from gcia.api.main import app
from gcia.common.config import settings
from gcia.common.context import Budget, RunContext
from gcia.common.model_gateway import ModelGateway, MockProvider


def _context() -> RunContext:
    return RunContext(
        tenant_id="test",
        budget=Budget(max_tokens=1000, max_cost_usd=1.0),
        model_gateway=ModelGateway(provider=MockProvider()),
    )


def test_resolves_known_alias_to_canonical_company():
    result = CompanyEntityAgent().run("ACME", _context())
    assert result.company.company_id == "acme-corp"
    assert result.matched_on == "alias"
    assert result.confidence > 0.5


def test_resolves_known_ticker():
    result = CompanyEntityAgent().run("ACM", _context())
    assert result.company.company_id == "acme-corp"
    assert result.matched_on == "ticker"


def test_resolves_canonical_name_case_insensitively():
    result = CompanyEntityAgent().run("acme corp", _context())
    assert result.company.company_id == "acme-corp"
    assert result.matched_on == "exact_name"
    assert result.confidence == 1.0


def test_unknown_identifier_resolves_to_new_entity_rather_than_failing():
    result = CompanyEntityAgent().run("Some Totally New Company", _context())
    assert result.matched_on == "new"
    assert result.company.canonical_name == "Some Totally New Company"
    assert result.confidence < 1.0


def test_resolve_company_api_endpoint():
    settings.gcia_api_keys = ""
    client = TestClient(app)
    res = client.post("/v1/resolve-company", json={"query": "ACME"})
    assert res.status_code == 200
    body = res.json()
    assert body["company_id"] == "acme-corp"
    assert body["is_new_entity"] is False
