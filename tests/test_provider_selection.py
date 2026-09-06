from __future__ import annotations

from gcia.common.config import settings
from gcia.common.model_gateway import (
    AnthropicProvider,
    MockProvider,
    ModelGateway,
    OpenAIProvider,
    resolve_provider,
)


def _reset_settings():
    settings.gcia_model_provider = "anthropic"
    settings.anthropic_api_key = None
    settings.openai_api_key = None


def test_defaults_to_mock_when_no_key_configured():
    _reset_settings()
    try:
        provider = resolve_provider({"answer": "placeholder"})
        assert isinstance(provider, MockProvider)
    finally:
        _reset_settings()


def test_resolves_anthropic_when_key_present_and_provider_is_anthropic():
    _reset_settings()
    try:
        settings.anthropic_api_key = "fake-key-for-test"
        provider = resolve_provider({})
        assert isinstance(provider, AnthropicProvider)
    finally:
        _reset_settings()


def test_resolves_openai_when_key_present_and_provider_is_openai():
    _reset_settings()
    try:
        settings.gcia_model_provider = "openai"
        settings.openai_api_key = "fake-key-for-test"
        provider = resolve_provider({})
        assert isinstance(provider, OpenAIProvider)
    finally:
        _reset_settings()


def test_falls_back_to_mock_when_openai_selected_but_no_key():
    _reset_settings()
    try:
        settings.gcia_model_provider = "openai"
        provider = resolve_provider({"answer": "placeholder"})
        assert isinstance(provider, MockProvider)
    finally:
        _reset_settings()


def test_model_gateway_picks_openai_model_names_for_openai_provider():
    settings.gcia_openai_model_small = "gpt-4o-mini"
    settings.gcia_openai_model_large = "gpt-4o"
    gateway = ModelGateway(provider=MockProvider(), provider_kind="openai")

    assert gateway._model_for("small") == "gpt-4o-mini"
    assert gateway._model_for("large") == "gpt-4o"


def test_model_gateway_picks_anthropic_model_names_by_default():
    gateway = ModelGateway(provider=MockProvider(), provider_kind="anthropic")

    assert gateway._model_for("small") == settings.gcia_model_small
    assert gateway._model_for("large") == settings.gcia_model_large
