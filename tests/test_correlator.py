"""Tests for logslice.correlator."""

import pytest

from logslice.correlator import LogCorrelator


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _e(cid, level="INFO", msg="hello"):
    entry = {"level": level, "message": msg}
    if cid is not None:
        entry["correlation_id"] = cid
    return entry


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------

def test_default_field():
    c = LogCorrelator()
    assert c.field == "correlation_id"


def test_custom_field_stored():
    c = LogCorrelator(field="trace_id")
    assert c.field == "trace_id"


def test_empty_field_raises():
    with pytest.raises(ValueError):
        LogCorrelator(field="")


def test_default_missing_label():
    c = LogCorrelator()
    assert c.missing == "unknown"


def test_custom_missing_label():
    c = LogCorrelator(missing="none")
    assert c.missing == "none"


# ---------------------------------------------------------------------------
# feed / feed_many
# ---------------------------------------------------------------------------

def test_feed_returns_key():
    c = LogCorrelator()
    key = c.feed(_e("abc-123"))
    assert key == "abc-123"


def test_feed_missing_field_uses_unknown():
    c = LogCorrelator()
    key = c.feed(_e(None))
    assert key == "unknown"


def test_feed_many_returns_self():
    c = LogCorrelator()
    result = c.feed_many([_e("x"), _e("y")])
    assert result is c


def test_groups_populated_after_feed():
    c = LogCorrelator()
    c.feed_many([_e("a"), _e("a"), _e("b")])
    g = c.groups()
    assert len(g["a"]) == 2
    assert len(g["b"]) == 1


def test_get_returns_entries_for_key():
    c = LogCorrelator()
    e1 = _e("req-1")
    e2 = _e("req-1", level="ERROR")
    c.feed_many([e1, e2])
    result = c.get("req-1")
    assert result == [e1, e2]


def test_get_unknown_key_returns_empty():
    c = LogCorrelator()
    assert c.get("nonexistent") == []


def test_keys_sorted():
    c = LogCorrelator()
    c.feed_many([_e("z"), _e("a"), _e("m")])
    assert c.keys() == ["a", "m", "z"]


def test_stream_yields_correct_entries():
    c = LogCorrelator()
    entries = [_e("r1"), _e("r1", level="WARN")]
    c.feed_many(entries)
    streamed = list(c.stream("r1"))
    assert streamed == entries


def test_stream_unknown_key_yields_nothing():
    c = LogCorrelator()
    assert list(c.stream("missing")) == []


# ---------------------------------------------------------------------------
# transform
# ---------------------------------------------------------------------------

def test_transform_applied_to_key():
    c = LogCorrelator(transform=str.upper)
    key = c.feed(_e("abc"))
    assert key == "ABC"
    assert "ABC" in c.groups()


# ---------------------------------------------------------------------------
# reset
# ---------------------------------------------------------------------------

def test_reset_clears_groups():
    c = LogCorrelator()
    c.feed_many([_e("x"), _e("y")])
    result = c.reset()
    assert c.groups() == {}
    assert result is c
