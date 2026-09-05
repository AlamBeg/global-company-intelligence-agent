"""Uniform agent interface.

Every agent - deterministic or LLM-backed, Lane 1/2/3 - implements Agent so
the pipeline runners can retry, log, and dead-letter all 21 agent
responsibilities identically. See docs/MULTI_AGENT_ARCHITECTURE.md
"Agent interface contract".
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from gcia.common.context import RunContext

TIn = TypeVar("TIn")
TOut = TypeVar("TOut")


class ModelTier:
    """Cost tier for an agent's model usage.

    NONE  - no LLM call; deterministic/statistical/rule-based.
    SMALL - cheap, fast, high-volume model calls (per-item, Lane 1).
    LARGE - frontier reasoning model, reserved for low-volume, high-value
            calls (per-cluster or on-demand, Lane 2/3).
    """

    NONE = "none"
    SMALL = "small"
    LARGE = "large"


class Agent(ABC, Generic[TIn, TOut]):
    name: str
    version: str
    tier: str = ModelTier.NONE

    @property
    def agent_id(self) -> str:
        return f"{self.name}:{self.version}"

    @abstractmethod
    def run(self, input: TIn, context: RunContext) -> TOut:
        """Execute the agent. Must be a pure function of (input, self.version)
        wherever tier is NONE; LLM-backed agents must still be deterministic
        about which model/prompt version they used, recorded via context.
        """
        raise NotImplementedError
