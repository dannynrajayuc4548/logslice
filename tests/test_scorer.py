"""Tests for logslice.scorer.LogScorer."""
import pytest

from logslice.scorer import LogScorer


def _e(**kwargs):
    base = {"level": "INFO", "message": "hello", "service": "api"}
    base.update(kwargs)
    return base


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------

def test_default_score_field():
    s = LogScorer()
    assert s.score_field == "_score"


def test_custom_score_field_stored():
    s = LogScorer(score_field="relevance")
    assert s.score_field == "relevance"


def test_empty_score_field_raises():
    with pytest.raises(ValueError):
        LogScorer(score_field="")


def test_default_score_default_is_zero():
    s = LogScorer()
    assert s.default_score == 0.0


def test_custom_default_score_stored():
    s = LogScorer(default_score=1.5)
    assert s.default_score == 1.5


# ---------------------------------------------------------------------------
# add_rule
# ---------------------------------------------------------------------------

def test_add_rule_returns_self():
    s = LogScorer()
    result = s.add_rule(lambda e: True, 1.0)
    assert result is s


def test_add_rule_non_callable_raises():
    with pytest.raises(TypeError):
        LogScorer().add_rule("not callable", 1.0)  # type: ignore


def test_rules_list_grows():
    s = LogScorer()
    s.add_rule(lambda e: True, 1.0)
    s.add_rule(lambda e: False, 2.0)
    assert len(s.rules) == 2


# ---------------------------------------------------------------------------
# score()
# ---------------------------------------------------------------------------

def test_no_rules_returns_default_score():
    s = LogScorer()
    result = s.score(_e())
    assert result["_score"] == 0.0


def test_matching_rule_adds_weight():
    s = LogScorer()
    s.add_rule(lambda e: e["level"] == "ERROR", 10.0)
    result = s.score(_e(level="ERROR"))
    assert result["_score"] == 10.0


def test_non_matching_rule_adds_nothing():
    s = LogScorer()
    s.add_rule(lambda e: e["level"] == "ERROR", 10.0)
    result = s.score(_e(level="INFO"))
    assert result["_score"] == 0.0


def test_multiple_rules_cumulative():
    s = LogScorer()
    s.add_rule(lambda e: e["level"] == "ERROR", 5.0)
    s.add_rule(lambda e: "fail" in e.get("message", ""), 3.0)
    result = s.score(_e(level="ERROR", message="fail hard"))
    assert result["_score"] == 8.0


def test_score_does_not_mutate_original():
    s = LogScorer()
    s.add_rule(lambda e: True, 1.0)
    entry = _e()
    s.score(entry)
    assert "_score" not in entry


# ---------------------------------------------------------------------------
# Convenience helpers
# ---------------------------------------------------------------------------

def test_field_equals_convenience():
    s = LogScorer()
    s.field_equals("level", "ERROR", 7.0)
    assert s.score(_e(level="ERROR"))["_score"] == 7.0
    assert s.score(_e(level="INFO"))["_score"] == 0.0


def test_field_contains_convenience():
    s = LogScorer()
    s.field_contains("message", "timeout", 4.0)
    assert s.score(_e(message="connection timeout"))["_score"] == 4.0
    assert s.score(_e(message="all good"))["_score"] == 0.0


# ---------------------------------------------------------------------------
# stream()
# ---------------------------------------------------------------------------

def test_stream_yields_all_when_no_threshold():
    s = LogScorer()
    entries = [_e(level="INFO"), _e(level="ERROR")]
    results = list(s.stream(entries))
    assert len(results) == 2


def test_stream_threshold_filters_low_scores():
    s = LogScorer()
    s.field_equals("level", "ERROR", 10.0)
    entries = [_e(level="INFO"), _e(level="ERROR"), _e(level="WARN")]
    results = list(s.stream(entries, threshold=5.0))
    assert len(results) == 1
    assert results[0]["level"] == "ERROR"


def test_stream_all_pass_when_threshold_is_zero():
    s = LogScorer()
    entries = [_e(), _e(), _e()]
    results = list(s.stream(entries, threshold=0.0))
    assert len(results) == 3


def test_stream_preserves_original_fields():
    s = LogScorer()
    s.add_rule(lambda e: True, 1.0)
    entry = _e(custom="value")
    result = next(s.stream([entry]))
    assert result["custom"] == "value"
    assert result["_score"] == 1.0
