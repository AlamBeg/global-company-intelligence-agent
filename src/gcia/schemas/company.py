from __future__ import annotations

from pydantic import BaseModel, Field


class EntityAlias(BaseModel):
    alias: str
    alias_type: str  # legal_name, brand, product, ticker, domain, local_name, misspelling
    language: str | None = None
    confidence: float = 1.0


class Company(BaseModel):
    company_id: str
    canonical_name: str
    aliases: list[EntityAlias] = Field(default_factory=list)
    tickers: list[str] = Field(default_factory=list)
    domains: list[str] = Field(default_factory=list)
    subsidiaries: list[str] = Field(default_factory=list)  # company_id references
    schema_version: str = "1.0"
