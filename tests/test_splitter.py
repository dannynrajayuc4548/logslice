"""Tests for logslice.splitter.LogSplitter."""

import pytest

from logslice.splitter import LogSplitter


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _e(level="INFO", msg="hello", **kwargs):
    entry = {"level": level, "message": msg}
    entry.update(kwargs)
    return entry


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------

def test_raises_on_empty_field():
    with pytest.raises(ValueError):
        LogSplitter("")


def test_default_bucket_name_is_unknown():
    s = LogSplitter("level")
    assert s.default == "unknown"


def test_custom_default_stored():
    s = LogSplitter("level", default="other")
    assert s.default == "other"


# ---------------------------------------------------------------------------
# feed()
# ---------------------------------------------------------------------------

def test_feed_splits_by_field():
    entries = [_e("INFO"), _e("ERROR"), _e("INFO")]
    s = LogSplitter("level").feed(entries)
    assert len(s.buckets["INFO"]) == 2
    assert len(s.buckets["ERROR"]) == 1


def test_missing_field_goes_to_default():
    entries = [{"message": "no level here"}]
    s = LogSplitter("level").feed(entries)
    assert "unknown" in s.buckets
    assert s.buckets["unknown"][0]["message"] == "no level here"


def test_feed_returns_self_for_chaining():
    s = LogSplitter("level")
    result = s.feed([_e()])
    assert result is s


def test_multiple_feeds_accumulate():
    s = LogSplitter("level")
    s.feed([_e("INFO")])
    s.feed([_e("INFO")])
    assert len(s.buckets["INFO"]) == 2


# ---------------------------------------------------------------------------
# transform
# ---------------------------------------------------------------------------

def test_transform_normalises_bucket_name():
    entries = [_e("INFO"), _e("info"), _e("Info")]
    s = LogSplitter("level", transform=str.lower).feed(entries)
    assert set(s.buckets.keys()) == {"info"}
    assert len(s.buckets["info"]) == 3


# ---------------------------------------------------------------------------
# stream()
# ---------------------------------------------------------------------------

def test_stream_yields_tuples():
    entries = [_e("INFO"), _e("ERROR")]
    s = LogSplitter("level")
    results = list(s.stream(entries))
    assert results[0] == ("INFO", entries[0])
    assert results[1] == ("ERROR", entries[1])


def test_stream_does_not_populate_buckets():
    entries = [_e("INFO")]
    s = LogSplitter("level")
    list(s.stream(entries))
    assert s.buckets == {}


# ---------------------------------------------------------------------------
# bucket_names() and clear()
# ---------------------------------------------------------------------------

def test_bucket_names_sorted():
    s = LogSplitter("level").feed([_e("WARN"), _e("DEBUG"), _e("ERROR")])
    assert s.bucket_names() == ["DEBUG", "ERROR", "WARN"]


def test_clear_resets_buckets():
    s = LogSplitter("level").feed([_e("INFO")])
    s.clear()
    assert s.buckets == {}


def test_clear_returns_self():
    s = LogSplitter("level")
    assert s.clear() is s
