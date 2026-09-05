"""Deterministic ID and content-address helpers.

Used to satisfy NFR-006 (idempotency): re-ingesting the same source item, or
re-running an agent with the same input and version, must not create
uncontrolled duplicate records.
"""
from __future__ import annotations

import hashlib


def discussion_id(platform: str, source_native_id: str) -> str:
    """Deterministic discussion ID from platform + the source's own record ID."""
    raw = f"{platform.strip().lower()}:{source_native_id.strip()}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:32]


def content_hash(text: str) -> str:
    """Hash of normalized content, used for near-duplicate bucketing and caching."""
    normalized = " ".join(text.split()).lower()
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def agent_output_key(input_hash: str, agent_name: str, agent_version: str) -> str:
    """Content address for an agent's output (see
    docs/MULTI_AGENT_ARCHITECTURE.md "Determinism and idempotency"):
    reprocessing after a version bump only recomputes keys that changed.
    """
    raw = f"{agent_name}:{agent_version}:{input_hash}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()
