"""Tests for LogSorter and SortPipeline."""
from __future__ import annotations

import json
import os
import tempfile

import pytest

from logslice.sorter import LogSorter
from logslice.sort_pipeline import SortPipeline
from logslice.filters import RegexFilter


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _e(ts: str, msg: str = "hello", level: str = "INFO") -> dict:
    return {"timestamp": ts, "message": msg, "level": level}


def _write_log(lines: list[dict]) -> str:
    fd, path = tempfile.mkstemp(suffix=".jsonl")
    with os.fdopen(fd, "w") as fh:
        for entry in lines:
            fh.write(json.dumps(entry) + "\n")
    return path


# ---------------------------------------------------------------------------
# LogSorter – construction
# ---------------------------------------------------------------------------

def test_default_field_is_timestamp():
    s = LogSorter()
    assert s.field == "timestamp"


def test_custom_field_stored():
    s = LogSorter(field="level")
    assert s.field == "level"


def test_empty_field_raises():
    with pytest.raises(ValueError):
        LogSorter(field="")


def test_whitespace_field_raises():
    with pytest.raises(ValueError):
        LogSorter(field="   ")


def test_default_reverse_is_false():
    assert LogSorter().reverse is False


def test_reverse_stored():
    assert LogSorter(reverse=True).reverse is True


def test_default_default_is_empty_string():
    assert LogSorter().default == ""


# ---------------------------------------------------------------------------
# LogSorter – sort behaviour
# ---------------------------------------------------------------------------

def test_sort_ascending():
    entries = [_e("2024-01-03"), _e("2024-01-01"), _e("2024-01-02")]
    result = LogSorter().sort(entries)
    assert [r["timestamp"] for r in result] == [
        "2024-01-01", "2024-01-02", "2024-01-03"
    ]


def test_sort_descending():
    entries = [_e("2024-01-01"), _e("2024-01-03"), _e("2024-01-02")]
    result = LogSorter(reverse=True).sort(entries)
    assert result[0]["timestamp"] == "2024-01-03"


def test_missing_key_uses_default():
    entries = [{"message": "no-ts"}, _e("2024-01-01")]
    result = LogSorter(default="0000-00-00").sort(entries)
    assert result[0]["message"] == "no-ts"


def test_custom_key_function():
    entries = [_e("b"), _e("a"), _e("c")]
    result = LogSorter(field="timestamp", key=str.lower).sort(entries)
    assert [r["timestamp"] for r in result] == ["a", "b", "c"]


def test_stream_yields_sorted():
    entries = [_e("2024-01-03"), _e("2024-01-01")]
    result = list(LogSorter().stream(entries))
    assert result[0]["timestamp"] == "2024-01-01"


def test_sort_does_not_mutate_input():
    entries = [_e("2024-01-02"), _e("2024-01-01")]
    original_order = [e["timestamp"] for e in entries]
    LogSorter().sort(entries)
    assert [e["timestamp"] for e in entries] == original_order


# ---------------------------------------------------------------------------
# SortPipeline
# ---------------------------------------------------------------------------

def test_pipeline_attribute_is_log_pipeline():
    from logslice.pipeline import LogPipeline
    path = _write_log([_e("2024-01-01")])
    sp = SortPipeline(path)
    assert isinstance(sp.pipeline, LogPipeline)
    os.unlink(path)


def test_sorter_attribute_is_log_sorter():
    path = _write_log([_e("2024-01-01")])
    sp = SortPipeline(path)
    assert isinstance(sp.sorter, LogSorter)
    os.unlink(path)


def test_collect_returns_sorted_list():
    entries = [_e("2024-01-03"), _e("2024-01-01"), _e("2024-01-02")]
    path = _write_log(entries)
    result = SortPipeline(path).collect()
    assert [r["timestamp"] for r in result] == [
        "2024-01-01", "2024-01-02", "2024-01-03"
    ]
    os.unlink(path)


def test_stream_yields_sorted_entries():
    entries = [_e("2024-01-02"), _e("2024-01-01")]
    path = _write_log(entries)
    result = list(SortPipeline(path).stream())
    assert result[0]["timestamp"] == "2024-01-01"
    os.unlink(path)


def test_add_filter_reduces_then_sorts():
    entries = [
        _e("2024-01-03", level="ERROR"),
        _e("2024-01-01", level="INFO"),
        _e("2024-01-02", level="ERROR"),
    ]
    path = _write_log(entries)
    sp = SortPipeline(path)
    sp.add_filter(RegexFilter("ERROR", field="level"))
    result = sp.collect()
    assert len(result) == 2
    assert result[0]["timestamp"] == "2024-01-02"
    os.unlink(path)


def test_add_filter_returns_self():
    path = _write_log([_e("2024-01-01")])
    sp = SortPipeline(path)
    assert sp.add_filter(RegexFilter(".")) is sp
    os.unlink(path)


def test_reverse_option_forwarded():
    entries = [_e("2024-01-01"), _e("2024-01-03"), _e("2024-01-02")]
    path = _write_log(entries)
    result = SortPipeline(path, reverse=True).collect()
    assert result[0]["timestamp"] == "2024-01-03"
    os.unlink(path)
