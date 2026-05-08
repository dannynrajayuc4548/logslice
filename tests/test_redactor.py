"""Tests for logslice.redactor.LogRedactor."""

import re
import pytest
from logslice.redactor import LogRedactor


def _entry(**kwargs):
    base = {"level": "INFO", "message": "hello", "user": "alice"}
    base.update(kwargs)
    return base


# ---------------------------------------------------------------------------
# mask_field
# ---------------------------------------------------------------------------

def test_mask_field_replaces_value():
    r = LogRedactor()
    r.mask_field("user")
    result = r.apply(_entry())
    assert result["user"] == "***"


def test_mask_field_custom_mask():
    r = LogRedactor()
    r.mask_field("user", mask="[REDACTED]")
    result = r.apply(_entry())
    assert result["user"] == "[REDACTED]"


def test_mask_field_missing_key_is_noop():
    r = LogRedactor()
    r.mask_field("password")
    entry = _entry()
    result = r.apply(entry)
    assert "password" not in result
    assert result == entry


def test_mask_does_not_mutate_original():
    r = LogRedactor().mask_field("user")
    original = _entry()
    r.apply(original)
    assert original["user"] == "alice"


# ---------------------------------------------------------------------------
# remove_field
# ---------------------------------------------------------------------------

def test_remove_field_deletes_key():
    r = LogRedactor().remove_field("user")
    result = r.apply(_entry())
    assert "user" not in result


def test_remove_field_missing_key_is_noop():
    r = LogRedactor().remove_field("token")
    entry = _entry()
    result = r.apply(entry)
    assert set(result.keys()) == set(entry.keys())


# ---------------------------------------------------------------------------
# regex_field
# ---------------------------------------------------------------------------

def test_regex_field_substitutes_pattern():
    r = LogRedactor().regex_field("message", r"\d+", "NUM")
    result = r.apply(_entry(message="user 42 logged in"))
    assert result["message"] == "user NUM logged in"


def test_regex_field_case_insensitive_flag():
    r = LogRedactor().regex_field("message", r"hello", "HI", flags=re.IGNORECASE)
    result = r.apply(_entry(message="HELLO world"))
    assert result["message"] == "HI world"


def test_regex_field_coerces_value_to_str():
    r = LogRedactor().regex_field("code", r"404", "XXX")
    result = r.apply(_entry(code=404))
    assert result["code"] == "XXX"


# ---------------------------------------------------------------------------
# chaining and stream
# ---------------------------------------------------------------------------

def test_chaining_returns_self():
    r = LogRedactor()
    assert r.mask_field("user") is r
    assert r.remove_field("level") is r
    assert r.regex_field("message", r"x") is r


def test_stream_yields_redacted_entries():
    r = LogRedactor().mask_field("user")
    entries = [_entry(user="alice"), _entry(user="bob")]
    results = list(r.stream(entries))
    assert all(e["user"] == "***" for e in results)
    assert len(results) == 2


def test_multiple_rules_applied_in_order():
    r = (
        LogRedactor()
        .mask_field("user")
        .remove_field("level")
        .regex_field("message", r"hello", "hi")
    )
    result = r.apply(_entry())
    assert result["user"] == "***"
    assert "level" not in result
    assert result["message"] == "hi"
