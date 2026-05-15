"""Tests for LogAnnotator."""
import pytest

from logslice.annotator import LogAnnotator


def _e(**kwargs):
    return {"timestamp": "2024-01-01T00:00:00", "level": "INFO", "message": "ok", **kwargs}


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------

def test_default_annotation_key():
    a = LogAnnotator()
    assert a.annotation_key == "annotations"


def test_custom_annotation_key_stored():
    a = LogAnnotator(annotation_key="meta")
    assert a.annotation_key == "meta"


def test_empty_annotation_key_raises():
    with pytest.raises(ValueError):
        LogAnnotator(annotation_key="")


def test_whitespace_annotation_key_raises():
    with pytest.raises(ValueError):
        LogAnnotator(annotation_key="   ")


# ---------------------------------------------------------------------------
# add_rule
# ---------------------------------------------------------------------------

def test_add_rule_returns_self():
    a = LogAnnotator()
    result = a.add_rule(lambda e: True, "flag", True)
    assert result is a


def test_empty_rule_key_raises():
    a = LogAnnotator()
    with pytest.raises(ValueError):
        a.add_rule(lambda e: True, "", True)


def test_rules_stored_in_order():
    a = LogAnnotator()
    a.add_rule(lambda e: True, "a", 1)
    a.add_rule(lambda e: True, "b", 2)
    keys = [r[1] for r in a.rules]
    assert keys == ["a", "b"]


# ---------------------------------------------------------------------------
# annotate
# ---------------------------------------------------------------------------

def test_matching_rule_adds_annotation():
    a = LogAnnotator()
    a.add_rule(lambda e: e.get("level") == "ERROR", "urgent", True)
    entry = _e(level="ERROR")
    result = a.annotate(entry)
    assert result["annotations"]["urgent"] is True


def test_non_matching_rule_skipped():
    a = LogAnnotator()
    a.add_rule(lambda e: e.get("level") == "ERROR", "urgent", True)
    entry = _e(level="INFO")
    result = a.annotate(entry)
    assert "urgent" not in result["annotations"]


def test_multiple_rules_applied():
    a = LogAnnotator()
    a.add_rule(lambda e: True, "seen", True)
    a.add_rule(lambda e: "fail" in e.get("message", ""), "category", "failure")
    entry = _e(message="fail fast")
    result = a.annotate(entry)
    assert result["annotations"]["seen"] is True
    assert result["annotations"]["category"] == "failure"


def test_annotate_does_not_mutate_original():
    a = LogAnnotator()
    a.add_rule(lambda e: True, "x", 1)
    entry = _e()
    a.annotate(entry)
    assert "annotations" not in entry


def test_existing_annotations_preserved():
    a = LogAnnotator()
    a.add_rule(lambda e: True, "new", 99)
    entry = _e(annotations={"old": "value"})
    result = a.annotate(entry)
    assert result["annotations"]["old"] == "value"
    assert result["annotations"]["new"] == 99


def test_predicate_exception_skipped():
    a = LogAnnotator()
    a.add_rule(lambda e: 1 / 0, "bad", True)  # will raise ZeroDivisionError
    entry = _e()
    result = a.annotate(entry)  # should not raise
    assert "bad" not in result["annotations"]


# ---------------------------------------------------------------------------
# apply (streaming)
# ---------------------------------------------------------------------------

def test_apply_yields_all_entries():
    a = LogAnnotator()
    entries = [_e(level="INFO"), _e(level="ERROR")]
    results = list(a.apply(entries))
    assert len(results) == 2


def test_apply_annotations_correct_per_entry():
    a = LogAnnotator()
    a.add_rule(lambda e: e.get("level") == "ERROR", "alert", True)
    entries = [_e(level="INFO"), _e(level="ERROR")]
    results = list(a.apply(entries))
    assert "alert" not in results[0]["annotations"]
    assert results[1]["annotations"]["alert"] is True


def test_custom_annotation_key_used():
    a = LogAnnotator(annotation_key="meta")
    a.add_rule(lambda e: True, "tagged", True)
    result = a.annotate(_e())
    assert "meta" in result
    assert result["meta"]["tagged"] is True
