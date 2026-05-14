"""Tests for LogClassifier."""
import pytest
from logslice.classifier import LogClassifier


def _e(**kw):
    return {"message": "test", "level": "INFO", **kw}


# ------------------------------------------------------------------
# Construction
# ------------------------------------------------------------------

def test_default_category_field():
    c = LogClassifier()
    assert c.category_field == "category"


def test_custom_category_field_stored():
    c = LogClassifier(category_field="kind")
    assert c.category_field == "kind"


def test_empty_category_field_raises():
    with pytest.raises(ValueError):
        LogClassifier(category_field="")


def test_whitespace_category_field_raises():
    with pytest.raises(ValueError):
        LogClassifier(category_field="   ")


def test_default_label_is_uncategorized():
    c = LogClassifier()
    assert c.default == "uncategorized"


def test_custom_default_stored():
    c = LogClassifier(default="other")
    assert c.default == "other"


# ------------------------------------------------------------------
# add_rule
# ------------------------------------------------------------------

def test_add_rule_returns_self():
    c = LogClassifier()
    result = c.add_rule("x", lambda e: True)
    assert result is c


def test_empty_rule_name_raises():
    with pytest.raises(ValueError):
        LogClassifier().add_rule("", lambda e: True)


def test_non_callable_predicate_raises():
    with pytest.raises(TypeError):
        LogClassifier().add_rule("r", "not_callable")  # type: ignore


def test_rules_property_returns_names_in_order():
    c = LogClassifier()
    c.add_rule("alpha", lambda e: False)
    c.add_rule("beta", lambda e: False)
    assert c.rules == ["alpha", "beta"]


# ------------------------------------------------------------------
# classify
# ------------------------------------------------------------------

def test_classify_applies_matching_rule():
    c = LogClassifier()
    c.add_rule("error", lambda e: e.get("level") == "ERROR")
    out = c.classify(_e(level="ERROR"))
    assert out["category"] == "error"


def test_classify_uses_default_when_no_match():
    c = LogClassifier()
    c.add_rule("error", lambda e: e.get("level") == "ERROR")
    out = c.classify(_e(level="INFO"))
    assert out["category"] == "uncategorized"


def test_classify_first_matching_rule_wins():
    c = LogClassifier()
    c.add_rule("first", lambda e: True)
    c.add_rule("second", lambda e: True)
    out = c.classify(_e())
    assert out["category"] == "first"


def test_classify_does_not_mutate_original():
    c = LogClassifier()
    c.add_rule("x", lambda e: True)
    entry = _e()
    c.classify(entry)
    assert "category" not in entry


def test_classify_custom_field_name():
    c = LogClassifier(category_field="kind")
    c.add_rule("warn", lambda e: e.get("level") == "WARN")
    out = c.classify(_e(level="WARN"))
    assert out["kind"] == "warn"
    assert "category" not in out


def test_predicate_exception_treated_as_no_match():
    c = LogClassifier()
    c.add_rule("boom", lambda e: 1 / 0)  # always raises
    c.add_rule("safe", lambda e: True)
    out = c.classify(_e())
    assert out["category"] == "safe"


# ------------------------------------------------------------------
# feed
# ------------------------------------------------------------------

def test_feed_yields_all_entries():
    c = LogClassifier()
    entries = [_e(level="ERROR"), _e(level="INFO")]
    result = list(c.feed(entries))
    assert len(result) == 2


def test_feed_classifies_each_entry():
    c = LogClassifier()
    c.add_rule("error", lambda e: e.get("level") == "ERROR")
    entries = [_e(level="ERROR"), _e(level="INFO")]
    result = list(c.feed(entries))
    assert result[0]["category"] == "error"
    assert result[1]["category"] == "uncategorized"
