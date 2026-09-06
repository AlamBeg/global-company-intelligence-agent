"""Runtime settings loaded from environment (.env in local dev)."""
from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Which vendor ModelGateway routes to: "anthropic" (default) or "openai".
    # Swappable because agents only ever call context.model_gateway.complete()
    # - never a vendor SDK directly.
    gcia_model_provider: str = "anthropic"

    anthropic_api_key: str | None = None
    gcia_model_small: str = "claude-haiku-4-5-20251001"
    gcia_model_large: str = "claude-sonnet-5"

    openai_api_key: str | None = None
    gcia_openai_model_small: str = "gpt-4o-mini"
    gcia_openai_model_large: str = "gpt-4o"

    gcia_max_tokens_per_run: int = 200_000
    gcia_max_cost_usd_per_run: float = 5.00

    # SQLite by default so the product runs with zero infra; switch to
    # postgresql://gcia:gcia@localhost:5432/gcia (docker-compose.yml) when
    # moving past a single-laptop demo.
    database_url: str = "sqlite:///./gcia.db"
    redis_url: str = "redis://localhost:6379/0"

    gcia_api_host: str = "0.0.0.0"
    gcia_api_port: int = 8000

    # RBAC (NFR-011): "key:role,key:role,..." e.g. "abc123:viewer,def456:admin".
    # Empty means no access control - fine for a single-laptop demo, but set
    # this before exposing the API beyond localhost.
    gcia_api_keys: str = ""


settings = Settings()
