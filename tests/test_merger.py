"""Tests for logslice.merger.LogMerger."""

from __future__ import annotations

import pytest

from logslice.merger import LogMerger


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _entries(*timestamps: str, level: str = "INFO") -> list:
    return [{"timestamp": ts, "level": level, "msg": f"msg-{ts}"} for ts in timestamps]


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_empty_merger_yields_nothing():
    merger = LogMerger()
    assert merger.collect() == []


def test_single_source_preserved_in_order():
    src = _entries("2024-01-01", "2024-01-02", "2024-01-03")
    result = LogMerger().add_source(src).collect()
    assert [e["timestamp"] for e in result] == ["2024-01-01", "2024-01-02", "2024-01-03"]


def test_two_sources_merged_chronologically():
    a = _entries("2024-01-01", "2024-01-03")
    b = _entries("2024-01-02", "2024-01-04")
    result = LogMerger().add_source(a).add_source(b).collect()
    assert [e["timestamp"] for e in result] == [
        "2024-01-01", "2024-01-02", "2024-01-03", "2024-01-04"
    ]


def test_three_sources_merged():
    a = _entries("2024-01-01", "2024-01-04")
    b = _entries("2024-01-02", "2024-01-05")
    c = _entries("2024-01-03", "2024-01-06")
    result = LogMerger().add_source(a).add_source(b).add_source(c).collect()
    timestamps = [e["timestamp"] for e in result]
    assert timestamps == sorted(timestamps)
    assert len(timestamps) == 6


def test_entries_missing_ts_key_sort_last():
    a = [{"msg": "no-ts"}]
    b = _entries("2024-01-01")
    result = LogMerger().add_source(a).add_source(b).collect()
    assert result[0]["timestamp"] == "2024-01-01"
    assert "timestamp" not in result[1]


def test_custom_key_fn():
    a = [{"seq": 3, "v": "a"}, {"seq": 1, "v": "b"}]
    b = [{"seq": 2, "v": "c"}, {"seq": 4, "v": "d"}]
    merger = LogMerger(key_fn=lambda e: e.get("seq", 9999))
    result = merger.add_source(a).add_source(b).collect()
    assert [e["seq"] for e in result] == [1, 2, 3, 4]


def test_add_source_returns_self_for_chaining():
    merger = LogMerger()
    returned = merger.add_source([])
    assert returned is merger


def test_stream_is_iterator():
    src = _entries("2024-01-01")
    merger = LogMerger().add_source(src)
    it = merger.stream()
    assert hasattr(it, "__iter__")
    assert hasattr(it, "__next__")


def test_custom_ts_key():
    src = [{"time": "2024-01-02", "msg": "b"}, {"time": "2024-01-01", "msg": "a"}]
    result = LogMerger(ts_key="time").add_source(src).collect()
    assert result[0]["time"] == "2024-01-01"
    assert result[1]["time"] == "2024-01-02"


def test_collect_returns_list():
    result = LogMerger().add_source(_entries("2024-01-01")).collect()
    assert isinstance(result, list)
