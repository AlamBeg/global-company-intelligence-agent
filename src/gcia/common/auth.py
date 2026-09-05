"""Role-based access control (NFR-011).

A minimal API-key -> role scheme for local/dev use. Production should swap
this for real auth (OAuth/JWT/SSO) behind the same `require_role` dependency
shape, so route code does not need to change - only this module does.
"""
from __future__ import annotations

from fastapi import Header, HTTPException

from gcia.common.config import settings

_ROLE_RANK = {"viewer": 0, "analyst": 1, "admin": 2}


def _load_api_keys() -> dict[str, str]:
    """Parses GCIA_API_KEYS="key1:viewer,key2:analyst,key3:admin" from env."""
    keys: dict[str, str] = {}
    for pair in settings.gcia_api_keys.split(","):
        pair = pair.strip()
        if not pair or ":" not in pair:
            continue
        key, role = (part.strip() for part in pair.split(":", 1))
        if role in _ROLE_RANK:
            keys[key] = role
    return keys


def require_role(minimum_role: str):
    """FastAPI dependency factory: enforces X-API-Key maps to a role at or
    above `minimum_role`, enforced at the API layer per NFR-011 - not only
    hidden in a UI.
    """
    if minimum_role not in _ROLE_RANK:
        raise ValueError(f"unknown role: {minimum_role!r}")

    def _dependency(x_api_key: str | None = Header(default=None)) -> str:
        api_keys = _load_api_keys()
        if not api_keys:
            # No keys configured: local/dev convenience only. Configure
            # GCIA_API_KEYS before exposing this beyond a single laptop.
            return "admin"
        if not x_api_key or x_api_key not in api_keys:
            raise HTTPException(status_code=401, detail="missing or invalid X-API-Key")
        role = api_keys[x_api_key]
        if _ROLE_RANK[role] < _ROLE_RANK[minimum_role]:
            raise HTTPException(status_code=403, detail=f"requires role '{minimum_role}' or higher")
        return role

    return _dependency
