from __future__ import annotations

from gcia.common.coercion import coerce_float_dict, coerce_str_list


def test_passes_through_real_numbers():
    assert coerce_float_dict({"pricing": 0.8, "support": -0.5}) == {
        "pricing": 0.8,
        "support": -0.5,
    }


def test_maps_known_label_words_to_scores():
    # This is the exact failure mode hit live with a local Ollama model:
    # aspect_sentiment came back as {"pricing": "positive"} instead of a number.
    result = coerce_float_dict({"pricing": "positive", "support": "negative"})
    assert result["pricing"] > 0
    assert result["support"] < 0


def test_parses_numeric_strings():
    assert coerce_float_dict({"pricing": "0.7"}) == {"pricing": 0.7}


def test_drops_unrecognized_values_without_raising():
    result = coerce_float_dict({"pricing": "extremely mixed feelings", "support": 0.5})
    assert result == {"support": 0.5}


def test_non_dict_input_returns_empty_dict():
    assert coerce_float_dict("not a dict") == {}
    assert coerce_float_dict(None) == {}


def test_booleans_are_not_treated_as_numbers():
    assert coerce_float_dict({"flag": True}) == {}


def test_str_list_passes_through_plain_strings():
    assert coerce_str_list(["purchase", "complaint"]) == ["purchase", "complaint"]


def test_str_list_extracts_name_from_wrapped_objects():
    # Exact failure mode hit live with a local Ollama model: IntentAgent's
    # "intents" list came back as [{"name": "purchase", "confidence": 0.8}]
    # instead of ["purchase"], crashing IntentAssessment validation.
    result = coerce_str_list([{"name": "purchase", "confidence": 0.8}, "complaint"])
    assert result == ["purchase", "complaint"]


def test_str_list_drops_unrecognized_entries_without_raising():
    assert coerce_str_list([{"confidence": 0.8}, 42, None]) == []


def test_str_list_non_list_input_returns_empty_list():
    assert coerce_str_list("not a list") == []
    assert coerce_str_list(None) == []
