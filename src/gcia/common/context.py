"""RunContext and budget enforcement.

Every agent call, whether deterministic or LLM-backed, receives a
RunContext. It is how the Orchestrator enforces per-run cost/token budgets
(docs/PRODUCT_REQUIREMENTS.md DoD "cost controls") without every agent
needing its own budget logic.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from gcia.common.model_gateway import ModelGateway


class BudgetExceededError(RuntimeError):
    """Raised when a run would exceed its configured token/cost budget."""


@dataclass
class Budget:
    max_tokens: int
    max_cost_usd: float
    spent_tokens: int = 0
    spent_cost_usd: float = 0.0

    def charge(self, tokens: int, cost_usd: float) -> None:
        if self.spent_tokens + tokens > self.max_tokens:
            raise BudgetExceededError(
                f"token budget exceeded: {self.spent_tokens + tokens} > {self.max_tokens}"
            )
        if self.spent_cost_usd + cost_usd > self.max_cost_usd:
            raise BudgetExceededError(
                f"cost budget exceeded: ${self.spent_cost_usd + cost_usd:.4f} > ${self.max_cost_usd:.2f}"
            )
        self.spent_tokens += tokens
        self.spent_cost_usd += cost_usd


@dataclass
class RunContext:
    tenant_id: str
    budget: Budget
    model_gateway: "ModelGateway"
    trace_id: str = field(default_factory=lambda: uuid.uuid4().hex)

    def child(self) -> "RunContext":
        """A sub-context for a nested call that should share budget/tenant but
        get its own trace id for tracing.
        """
        return RunContext(
            tenant_id=self.tenant_id,
            budget=self.budget,
            model_gateway=self.model_gateway,
            trace_id=f"{self.trace_id}.{uuid.uuid4().hex[:8]}",
        )
