"""Tests for LogAggregator."""

import pytest
from logslice.aggregator import LogAggregator


SAMPLE_ENTRIES = [
    {"level": "INFO",  "message": "started"},
    {"level": "DEBUG", "message": "connecting"},
    {"level": "INFO",  "message": "connected"},
    {"level": "ERROR", "message": "timeout"},
    {"level": "INFO",  "message": "retrying"},
    {"level": "ERROR", "message": "failed"},
]


def test_counts_by_level():
    agg = LogAggregator(key="level")
    agg.feed(SAMPLE_ENTRIES)
    counts = agg.counts()
    assert counts["INFO"] == 3
    assert counts["ERROR"] == 2
    assert counts["DEBUG"] == 1


def test_groups_contain_entries():
    agg = LogAggregator(key="level")
    agg.feed(SAMPLE_ENTRIES)
    groups = agg.groups()
    assert len(groups["INFO"]) == 3
    assert all(e["level"] == "ERROR" for e in groups["ERROR"])


def test_top_returns_sorted():
    agg = LogAggregator(key="level")
    agg.feed(SAMPLE_ENTRIES)
    top = agg.top(2)
    assert top[0][0] == "INFO"
    assert top[0][1] == 3
    assert len(top) == 2


def test_missing_key_uses_unknown():
    agg = LogAggregator(key="level")
    agg.feed([{"message": "no level here"}])
    assert "__unknown__" in agg.counts()


def test_transform_applied():
    agg = LogAggregator(key="level", transform=str.lower)
    agg.feed(SAMPLE_ENTRIES)
    assert "info" in agg.counts()
    assert "error" in agg.counts()


def test_reset_clears_data():
    agg = LogAggregator(key="level")
    agg.feed(SAMPLE_ENTRIES)
    agg.reset()
    assert agg.counts() == {}


def test_feed_multiple_times():
    agg = LogAggregator(key="level")
    agg.feed(SAMPLE_ENTRIES[:3])
    agg.feed(SAMPLE_ENTRIES[3:])
    assert agg.counts()["INFO"] == 3
