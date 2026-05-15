"""Tests for LogHighlighter."""
import re
import pytest
from logslice.highlighter import LogHighlighter


def _e(**kw):
    base = {"timestamp": "2024-01-01T00:00:00", "level": "INFO", "message": "hello"}
    base.update(kw)
    return base


# --- construction ---

def test_default_highlight_key():
    h = LogHighlighter()
    assert h.highlight_key == "_highlights"


def test_custom_highlight_key_stored():
    h = LogHighlighter(highlight_key="_marks")
    assert h.highlight_key == "_marks"


def test_empty_highlight_key_raises():
    with pytest.raises(ValueError):
        LogHighlighter(highlight_key="")


def test_whitespace_highlight_key_raises():
    with pytest.raises(ValueError):
        LogHighlighter(highlight_key="   ")


# --- add_rule ---

def test_add_rule_returns_self():
    h = LogHighlighter()
    assert h.add_rule("message", r"error") is h


def test_add_rule_empty_field_raises():
    with pytest.raises(ValueError):
        LogHighlighter().add_rule("", r"error")


def test_add_rule_empty_pattern_raises():
    with pytest.raises(ValueError):
        LogHighlighter().add_rule("message", "")


def test_rules_property_lists_registered_rules():
    h = LogHighlighter()
    h.add_rule("message", r"error").add_rule("level", r"WARN")
    assert h.rules == [("message", r"error"), ("level", r"WARN")]


# --- apply ---

def test_no_match_no_highlight_key():
    h = LogHighlighter()
    h.add_rule("message", r"ERROR")
    result = h.apply(_e(message="all good"))
    assert "_highlights" not in result


def test_match_adds_highlight_entry():
    h = LogHighlighter()
    h.add_rule("message", r"error", re.IGNORECASE)
    result = h.apply(_e(message="An ERROR occurred"))
    assert "_highlights" in result
    assert result["_highlights"][0]["field"] == "message"
    assert result["_highlights"][0]["match"] == "ERROR"


def test_multiple_matches_in_same_field():
    h = LogHighlighter()
    h.add_rule("message", r"\d+")
    result = h.apply(_e(message="retry 3 of 5"))
    matches = [hit["match"] for hit in result["_highlights"]]
    assert "3" in matches and "5" in matches


def test_missing_field_is_skipped():
    h = LogHighlighter()
    h.add_rule("nonexistent", r"error")
    result = h.apply(_e())
    assert "_highlights" not in result


def test_apply_does_not_mutate_original():
    h = LogHighlighter()
    h.add_rule("message", r"hello")
    entry = _e(message="hello world")
    h.apply(entry)
    assert "_highlights" not in entry


def test_custom_highlight_key_used_in_output():
    h = LogHighlighter(highlight_key="_marks")
    h.add_rule("message", r"hello")
    result = h.apply(_e(message="hello"))
    assert "_marks" in result
    assert "_highlights" not in result


# --- stream ---

def test_stream_yields_all_entries():
    h = LogHighlighter()
    h.add_rule("message", r"error")
    entries = [_e(message="no match"), _e(message="no match either")]
    out = list(h.stream(entries))
    assert len(out) == 2


def test_stream_annotates_matching_entries():
    h = LogHighlighter()
    h.add_rule("level", r"ERROR")
    entries = [_e(level="INFO"), _e(level="ERROR"), _e(level="WARN")]
    out = list(h.stream(entries))
    assert "_highlights" not in out[0]
    assert "_highlights" in out[1]
    assert "_highlights" not in out[2]
