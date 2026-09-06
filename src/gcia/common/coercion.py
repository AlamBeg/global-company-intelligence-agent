"""Defensive coercion for LLM output fields typed as dict[str, float].

Even with an explicit JSON schema hint, a model can drift - e.g. a local
model returning {"aspect_sentiment": {"pricing": "positive"}} instead of a
numeric score. This is applied regardless of provider (Anthropic/OpenAI can
drift too under edge cases); it is not an Ollama-specific workaround. The
alternative - letting pydantic validation crash the whole assessment on one
bad field - would throw away an otherwise-usable result.
"""
from __future__ import annotations

_LABEL_TO_SCORE = {
    "very positive": 1.0,
    "strongly positive": 1.0,
    "positive": 0.8,
    "slightly positive": 0.4,
    "neutral": 0.0,
    "mixed": 0.0,
    "slightly negative": -0.4,
    "negative": -0.8,
    "strongly negative": -1.0,
    "very negative": -1.0,
}


def coerce_float_dict(raw: object) -> dict[str, float]:
    """Best-effort conversion of a model's dict[str, Any] output into
    dict[str, float]. Unrecognized values are dropped rather than raised -
    a partially-populated result is more useful than a crashed pipeline.
    """
    if not isinstance(raw, dict):
        return {}
    result: dict[str, float] = {}
    for key, value in raw.items():
        if isinstance(value, bool):
            continue  # bool is a subclass of int in Python - exclude explicitly
        if isinstance(value, (int, float)):
            result[str(key)] = float(value)
            continue
        if isinstance(value, str):
            mapped = _LABEL_TO_SCORE.get(value.strip().lower())
            if mapped is not None:
                result[str(key)] = mapped
                continue
            try:
                result[str(key)] = float(value)
            except ValueError:
                pass  # unrecognized string label: skip this entry, keep the rest
    return result
