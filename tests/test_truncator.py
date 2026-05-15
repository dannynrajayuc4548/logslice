"""Tests for logslice.truncator."""
from __future__ import annotations

import pytest

from logslice.truncator import LogTruncator


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _e(**kwargs):
    base = {"level": "INFO", "message": "hello", "timestamp": "2024-01-01T00:00:00Z"}
    base.update(kwargs)
    return base


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------

def test_default_max_length():
    t = LogTruncator()
    assert t.max_length == 200


def test_custom_max_length_stored():
    t = LogTruncator(max_length=50)
    assert t.max_length == 50


def test_default_suffix():
    t = LogTruncator()
    assert t.suffix == "..."


def test_custom_suffix_stored():
    t = LogTruncator(suffix="[cut]")
    assert t.suffix == "[cut]"


def test_zero_max_length_raises():
    with pytest.raises(ValueError, match="positive integer"):
        LogTruncator(max_length=0)


def test_negative_max_length_raises():
    with pytest.raises(ValueError, match="positive integer"):
        LogTruncator(max_length=-5)


# ---------------------------------------------------------------------------
# add_field
# ---------------------------------------------------------------------------

def test_add_field_returns_self():
    t = LogTruncator()
    assert t.add_field("message") is t


def test_add_field_empty_raises():
    with pytest.raises(ValueError, match="empty or whitespace"):
        LogTruncator().add_field("")


def test_add_field_whitespace_raises():
    with pytest.raises(ValueError, match="empty or whitespace"):
        LogTruncator().add_field("   ")


def test_fields_list_reflects_additions():
    t = LogTruncator().add_field("message").add_field("body")
    assert t.fields == ["message", "body"]


def test_duplicate_field_not_added_twice():
    t = LogTruncator().add_field("message").add_field("message")
    assert t.fields.count("message") == 1


# ---------------------------------------------------------------------------
# apply
# ---------------------------------------------------------------------------

def test_short_value_unchanged():
    t = LogTruncator(max_length=20).add_field("message")
    entry = _e(message="short")
    assert t.apply(entry)["message"] == "short"


def test_long_value_truncated():
    t = LogTruncator(max_length=10, suffix="...").add_field("message")
    entry = _e(message="a" * 20)
    result = t.apply(entry)["message"]
    assert len(result) == 10
    assert result.endswith("...")


def test_exact_length_not_truncated():
    t = LogTruncator(max_length=5).add_field("message")
    entry = _e(message="abcde")
    assert t.apply(entry)["message"] == "abcde"


def test_non_string_field_untouched():
    t = LogTruncator(max_length=3).add_field("count")
    entry = _e(count=99999)
    assert t.apply(entry)["count"] == 99999


def test_missing_field_is_noop():
    t = LogTruncator(max_length=5).add_field("body")
    entry = _e()
    result = t.apply(entry)
    assert "body" not in result


def test_apply_does_not_mutate_original():
    t = LogTruncator(max_length=5, suffix="!").add_field("message")
    entry = _e(message="hello world")
    t.apply(entry)
    assert entry["message"] == "hello world"


def test_unregistered_field_not_truncated():
    t = LogTruncator(max_length=3).add_field("message")
    long_val = "x" * 50
    entry = _e(body=long_val)
    assert t.apply(entry)["body"] == long_val


# ---------------------------------------------------------------------------
# stream
# ---------------------------------------------------------------------------

def test_stream_yields_all_entries():
    t = LogTruncator(max_length=10).add_field("message")
    entries = [_e(message="a" * 20) for _ in range(5)]
    results = list(t.stream(entries))
    assert len(results) == 5


def test_stream_truncates_each_entry():
    t = LogTruncator(max_length=5, suffix=">").add_field("message")
    entries = [_e(message="hello world"), _e(message="hi")]
    results = list(t.stream(entries))
    assert results[0]["message"] == "hell>"
    assert results[1]["message"] == "hi"
