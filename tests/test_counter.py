"""Tests for logslice.counter.LogCounter."""
import pytest

from logslice.counter import LogCounter


def _entries(*levels):
    return [{"level": lvl, "message": f"msg {i}"} for i, lvl in enumerate(levels)]


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------

def test_default_field_is_level():
    c = LogCounter()
    assert c.field == "level"


def test_custom_field_stored():
    c = LogCounter(field="service")
    assert c.field == "service"


def test_empty_field_raises():
    with pytest.raises(ValueError):
        LogCounter(field="")


def test_default_label_is_unknown():
    c = LogCounter()
    assert c.default == "unknown"


def test_custom_default_stored():
    c = LogCounter(default="n/a")
    assert c.default == "n/a"


# ---------------------------------------------------------------------------
# Counting
# ---------------------------------------------------------------------------

def test_total_starts_at_zero():
    assert LogCounter().total == 0


def test_feed_increments_total():
    c = LogCounter()
    c.feed({"level": "INFO"})
    c.feed({"level": "ERROR"})
    assert c.total == 2


def test_counts_by_field():
    c = LogCounter()
    c.feed_many(_entries("INFO", "INFO", "ERROR", "WARN", "INFO"))
    result = c.counts()
    assert result["INFO"] == 3
    assert result["ERROR"] == 1
    assert result["WARN"] == 1


def test_missing_field_uses_default():
    c = LogCounter(field="service", default="unknown")
    c.feed({"message": "no service key"})
    assert c.counts()["unknown"] == 1


def test_none_value_uses_default():
    c = LogCounter(default="none_label")
    c.feed({"level": None})
    assert c.counts()["none_label"] == 1


def test_transform_applied():
    c = LogCounter(transform=str.lower)
    c.feed_many(_entries("INFO", "info", "Info"))
    assert c.counts()["info"] == 3


# ---------------------------------------------------------------------------
# top()
# ---------------------------------------------------------------------------

def test_top_returns_sorted_descending():
    c = LogCounter()
    c.feed_many(_entries("A", "A", "A", "B", "B", "C"))
    top = c.top(2)
    assert top[0] == ("A", 3)
    assert top[1] == ("B", 2)


def test_top_n_limits_results():
    c = LogCounter()
    c.feed_many(_entries("X", "Y", "Z"))
    assert len(c.top(2)) == 2


# ---------------------------------------------------------------------------
# reset()
# ---------------------------------------------------------------------------

def test_reset_clears_counts():
    c = LogCounter()
    c.feed_many(_entries("INFO", "ERROR"))
    c.reset()
    assert c.counts() == {}
    assert c.total == 0


def test_reset_returns_self():
    c = LogCounter()
    assert c.reset() is c


# ---------------------------------------------------------------------------
# stream()
# ---------------------------------------------------------------------------

def test_stream_yields_all_entries():
    c = LogCounter()
    entries = _entries("INFO", "ERROR", "WARN")
    result = list(c.stream(entries))
    assert len(result) == 3


def test_stream_counts_as_it_passes():
    c = LogCounter()
    entries = _entries("INFO", "INFO", "ERROR")
    list(c.stream(entries))
    assert c.counts()["INFO"] == 2
    assert c.counts()["ERROR"] == 1
