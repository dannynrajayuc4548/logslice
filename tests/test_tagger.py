"""Tests for logslice.tagger."""
import re
import pytest
from logslice.tagger import LogTagger


def _e(**kwargs) -> dict:
    base = {"level": "INFO", "message": "hello", "service": "web"}
    base.update(kwargs)
    return base


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------

def test_default_tag_field():
    t = LogTagger()
    assert t.tag_field == "tags"


def test_custom_tag_field_stored():
    t = LogTagger(tag_field="labels")
    assert t.tag_field == "labels"


def test_empty_tag_field_raises():
    with pytest.raises(ValueError, match="tag_field"):
        LogTagger(tag_field="")


# ---------------------------------------------------------------------------
# add_rule
# ---------------------------------------------------------------------------

def test_add_rule_returns_self():
    t = LogTagger()
    result = t.add_rule("x", lambda e: True)
    assert result is t


def test_add_rule_empty_tag_raises():
    with pytest.raises(ValueError, match="tag"):
        LogTagger().add_rule("", lambda e: True)


def test_rules_list_grows():
    t = LogTagger()
    t.add_rule("a", lambda e: True)
    t.add_rule("b", lambda e: False)
    assert len(t.rules) == 2


# ---------------------------------------------------------------------------
# tag_if_matches
# ---------------------------------------------------------------------------

def test_tag_if_matches_string_pattern():
    t = LogTagger()
    t.tag_if_matches("error-tag", "message", r"error")
    entry = _e(message="an error occurred")
    result = t.apply(entry)
    assert "error-tag" in result["tags"]


def test_tag_if_matches_compiled_pattern():
    t = LogTagger()
    t.tag_if_matches("warn-tag", "level", re.compile(r"WARN", re.IGNORECASE))
    result = t.apply(_e(level="warning"))
    assert "warn-tag" in result["tags"]


def test_tag_if_matches_no_match_not_tagged():
    t = LogTagger()
    t.tag_if_matches("error-tag", "message", r"critical")
    result = t.apply(_e(message="all good"))
    assert "error-tag" not in result["tags"]


# ---------------------------------------------------------------------------
# tag_if_field_equals
# ---------------------------------------------------------------------------

def test_tag_if_field_equals_match():
    t = LogTagger()
    t.tag_if_field_equals("critical", "level", "ERROR")
    result = t.apply(_e(level="ERROR"))
    assert "critical" in result["tags"]


def test_tag_if_field_equals_no_match():
    t = LogTagger()
    t.tag_if_field_equals("critical", "level", "ERROR")
    result = t.apply(_e(level="INFO"))
    assert "critical" not in result["tags"]


# ---------------------------------------------------------------------------
# apply / mutation safety
# ---------------------------------------------------------------------------

def test_apply_does_not_mutate_original():
    t = LogTagger()
    t.add_rule("x", lambda e: True)
    entry = _e()
    t.apply(entry)
    assert "tags" not in entry


def test_apply_accumulates_multiple_tags():
    t = LogTagger()
    t.tag_if_field_equals("svc-web", "service", "web")
    t.tag_if_matches("greeting", "message", r"hello")
    result = t.apply(_e())
    assert "svc-web" in result["tags"]
    assert "greeting" in result["tags"]


def test_apply_appends_to_existing_tags_list():
    t = LogTagger()
    t.tag_if_field_equals("new-tag", "level", "INFO")
    entry = _e(tags=["existing"])
    result = t.apply(entry)
    assert "existing" in result["tags"]
    assert "new-tag" in result["tags"]


def test_apply_no_duplicate_tags():
    t = LogTagger()
    t.tag_if_field_equals("dup", "level", "INFO")
    t.tag_if_field_equals("dup", "level", "INFO")
    result = t.apply(_e())
    assert result["tags"].count("dup") == 1


# ---------------------------------------------------------------------------
# stream
# ---------------------------------------------------------------------------

def test_stream_yields_all_entries():
    t = LogTagger()
    entries = [_e(), _e(level="ERROR")]
    results = list(t.stream(entries))
    assert len(results) == 2


def test_stream_tags_applied_to_each():
    t = LogTagger()
    t.tag_if_field_equals("err", "level", "ERROR")
    entries = [_e(level="INFO"), _e(level="ERROR"), _e(level="ERROR")]
    results = list(t.stream(entries))
    assert results[0]["tags"] == []
    assert results[1]["tags"] == ["err"]
    assert results[2]["tags"] == ["err"]


def test_stream_custom_tag_field():
    t = LogTagger(tag_field="labels")
    t.add_rule("always", lambda e: True)
    results = list(t.stream([_e()]))
    assert "always" in results[0]["labels"]
