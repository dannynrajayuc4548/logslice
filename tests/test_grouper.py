"""Tests for logslice.grouper.LogGrouper."""
import pytest
from logslice.grouper import LogGrouper


def _e(level="info", **kw):
    return {"level": level, "message": "msg", **kw}


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------

def test_default_field_is_level():
    g = LogGrouper()
    assert g.field == "level"


def test_custom_field_stored():
    g = LogGrouper(field="service")
    assert g.field == "service"


def test_empty_field_raises():
    with pytest.raises(ValueError):
        LogGrouper(field="")


def test_whitespace_field_raises():
    with pytest.raises(ValueError):
        LogGrouper(field="   ")


def test_default_default_label():
    g = LogGrouper()
    assert g.default == "unknown"


def test_custom_default_stored():
    g = LogGrouper(default="other")
    assert g.default == "other"


def test_empty_default_raises():
    with pytest.raises(ValueError):
        LogGrouper(default="")


# ---------------------------------------------------------------------------
# feed / buckets
# ---------------------------------------------------------------------------

def test_feed_returns_bucket_key():
    g = LogGrouper()
    key = g.feed(_e("error"))
    assert key == "error"


def test_feed_populates_bucket():
    g = LogGrouper()
    g.feed(_e("warn"))
    g.feed(_e("warn"))
    assert len(g.buckets["warn"]) == 2


def test_missing_field_uses_default():
    g = LogGrouper()
    entry = {"message": "no level here"}
    key = g.feed(entry)
    assert key == "unknown"


def test_none_value_uses_default():
    g = LogGrouper()
    key = g.feed({"level": None})
    assert key == "unknown"


def test_feed_many_returns_counts():
    g = LogGrouper()
    entries = [_e("info"), _e("info"), _e("error")]
    counts = g.feed_many(entries)
    assert counts == {"info": 2, "error": 1}


# ---------------------------------------------------------------------------
# stream / keys / clear
# ---------------------------------------------------------------------------

def test_stream_yields_entries_for_key():
    g = LogGrouper()
    g.feed(_e("debug"))
    g.feed(_e("debug"))
    result = list(g.stream("debug"))
    assert len(result) == 2


def test_stream_unknown_key_yields_nothing():
    g = LogGrouper()
    assert list(g.stream("nonexistent")) == []


def test_keys_returns_sorted_list():
    g = LogGrouper()
    g.feed(_e("warn"))
    g.feed(_e("info"))
    g.feed(_e("error"))
    assert g.keys() == ["error", "info", "warn"]


def test_clear_empties_all_buckets():
    g = LogGrouper()
    g.feed(_e("info"))
    g.clear()
    assert g.buckets == {}


# ---------------------------------------------------------------------------
# on_group hooks
# ---------------------------------------------------------------------------

def test_hook_called_for_matching_key():
    g = LogGrouper()
    seen = []
    g.on_group("error", seen.append)
    g.feed(_e("error"))
    assert len(seen) == 1


def test_hook_not_called_for_other_key():
    g = LogGrouper()
    seen = []
    g.on_group("error", seen.append)
    g.feed(_e("info"))
    assert seen == []


def test_non_callable_hook_raises():
    g = LogGrouper()
    with pytest.raises(TypeError):
        g.on_group("info", "not_callable")


def test_on_group_returns_self():
    g = LogGrouper()
    assert g.on_group("info", lambda e: None) is g
