from __future__ import annotations

from gcia.common.model_gateway import _strip_code_fences


def test_passes_through_raw_json_unchanged():
    assert _strip_code_fences('{"ok": true}') == '{"ok": true}'


def test_strips_json_language_tagged_fence():
    # The exact failure mode hit live with the real Anthropic API: Claude
    # wrapped a JSON reply in a ```json fence even when told to return raw
    # JSON, and json.loads() raised "Expecting value: line 1 column 1".
    text = '```json\n{"ok": true}\n```'
    assert _strip_code_fences(text) == '{"ok": true}'


def test_strips_bare_fence_without_language_tag():
    text = '```\n{"ok": true}\n```'
    assert _strip_code_fences(text) == '{"ok": true}'


def test_strips_surrounding_whitespace():
    text = '  \n```json\n{"ok": true}\n```\n  '
    assert _strip_code_fences(text) == '{"ok": true}'


def test_discards_prose_after_the_closing_fence():
    # The exact failure mode hit live: IntentAgent's real Claude response was
    # a fenced JSON block followed by an explanation paragraph. An anchored
    # regex (requiring the fence to span the whole string) missed this and
    # fell through to parsing the raw text, still starting with a backtick.
    text = (
        '```json\n{"intents": [], "confidence": 0.95}\n```\n\n'
        "This text is a factual statement with no behavioral intent signal."
    )
    assert _strip_code_fences(text) == '{"intents": [], "confidence": 0.95}'


def test_discards_prose_before_the_opening_fence():
    text = 'Here is the JSON:\n```json\n{"ok": true}\n```'
    assert _strip_code_fences(text) == '{"ok": true}'
