"""Model gateway: the single place every LLM call passes through.

Responsibilities (docs/SYSTEM_ARCHITECTURE.md section 7 and
MULTI_AGENT_ARCHITECTURE.md "LLM agents specifically"):
  - route a call to the right cost tier (small vs. large model)
  - record model, version, latency, and token/cost estimates
  - enforce structured output (JSON), never freeform prose passed downstream
  - support a cascade: try the small/cheap model first, escalate to the
    large model only when confidence is below threshold, instead of every
    agent defaulting to the frontier model on every call

This module has no dependency on any single agent. Agents call
`context.model_gateway.complete(...)`; they never talk to the Anthropic SDK
directly, so provider/model swaps and cost accounting stay in one place.
"""
from __future__ import annotations

import hashlib
import json
import logging
import time
from dataclasses import dataclass
from typing import Any, Protocol

from gcia.common.agent import ModelTier
from gcia.common.config import settings
from gcia.common.context import RunContext

logger = logging.getLogger("gcia.model_gateway")

# Anthropic's published per-token pricing changes over time; this is a rough
# planning estimate for cost budgeting only, not a billing source of truth.
_APPROX_COST_PER_1K_TOKENS_USD = {
    ModelTier.SMALL: 0.001,
    ModelTier.LARGE: 0.015,
}


@dataclass
class ModelCallResult:
    tier: str
    model: str
    output: dict[str, Any]
    input_tokens: int
    output_tokens: int
    cost_usd: float
    latency_ms: float
    cache_hit: bool = False


class Provider(Protocol):
    def complete_json(
        self, *, model: str, system: str, prompt: str, schema_hint: str
    ) -> tuple[dict[str, Any], int, int]:
        """Return (parsed_json, input_tokens, output_tokens)."""
        ...


class AnthropicProvider:
    """Thin wrapper over the Claude API. The SDK is imported lazily so the
    rest of the codebase - and tests, via MockProvider - never require an
    API key just to import this module.
    """

    def complete_json(
        self, *, model: str, system: str, prompt: str, schema_hint: str
    ) -> tuple[dict[str, Any], int, int]:
        import anthropic

        if not settings.anthropic_api_key:
            raise RuntimeError(
                "ANTHROPIC_API_KEY is not set; configure it in .env before using AnthropicProvider"
            )
        client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        response = client.messages.create(
            model=model,
            max_tokens=1024,
            system=f"{system}\n\nRespond with JSON matching this shape:\n{schema_hint}",
            messages=[{"role": "user", "content": prompt}],
        )
        text = "".join(block.text for block in response.content if block.type == "text")
        parsed = json.loads(text)
        return parsed, response.usage.input_tokens, response.usage.output_tokens


class MockProvider:
    """Deterministic stand-in for tests and local dev without API access."""

    def __init__(self, fixed_response: dict[str, Any] | None = None):
        self.fixed_response = fixed_response or {"label": "neutral", "confidence": 0.5}
        self.calls = 0

    def complete_json(
        self, *, model: str, system: str, prompt: str, schema_hint: str
    ) -> tuple[dict[str, Any], int, int]:
        self.calls += 1
        return (
            dict(self.fixed_response),
            len(prompt.split()),
            len(json.dumps(self.fixed_response).split()),
        )


class ModelGateway:
    def __init__(self, provider: Provider | None = None):
        self.provider = provider or AnthropicProvider()
        self._cache: dict[str, ModelCallResult] = {}

    def _model_for(self, tier: str) -> str:
        if tier == ModelTier.SMALL:
            return settings.gcia_model_small
        if tier == ModelTier.LARGE:
            return settings.gcia_model_large
        raise ValueError(f"tier {tier!r} has no model (deterministic agents should not call complete())")

    def complete(
        self,
        *,
        tier: str,
        system: str,
        prompt: str,
        schema_hint: str,
        context: RunContext,
        cache_key: str | None = None,
    ) -> ModelCallResult:
        """Structured-output call through the gateway.

        `cache_key`, when given (typically a content hash), lets repeated
        calls for identical input + prompt version skip the model entirely -
        the cheapest possible cost lever. Production should back this with
        Anthropic prompt caching (cache_control on the system block) in
        addition to this in-process cache.
        """
        key = cache_key and f"{tier}:{self._model_for(tier)}:{cache_key}"
        if key and key in self._cache:
            logger.info("model_gateway.cache_hit", extra={"trace_id": context.trace_id, "key": key})
            return self._cache[key]

        model = self._model_for(tier)
        start = time.perf_counter()
        output, input_tokens, output_tokens = self.provider.complete_json(
            model=model, system=system, prompt=prompt, schema_hint=schema_hint
        )
        latency_ms = (time.perf_counter() - start) * 1000

        cost_per_1k = _APPROX_COST_PER_1K_TOKENS_USD.get(tier, 0.0)
        cost_usd = ((input_tokens + output_tokens) / 1000) * cost_per_1k
        context.budget.charge(tokens=input_tokens + output_tokens, cost_usd=cost_usd)

        result = ModelCallResult(
            tier=tier,
            model=model,
            output=output,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost_usd,
            latency_ms=latency_ms,
        )
        logger.info(
            "model_gateway.call",
            extra={
                "trace_id": context.trace_id,
                "tenant_id": context.tenant_id,
                "tier": tier,
                "model": model,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "cost_usd": cost_usd,
                "latency_ms": latency_ms,
            },
        )
        if key:
            self._cache[key] = result
        return result


def prompt_cache_key(*parts: str) -> str:
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()
