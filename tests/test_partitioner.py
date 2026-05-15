"""Tests for logslice.partitioner."""
from __future__ import annotations

import pytest
from logslice.partitioner import LogPartitioner


def _e(ts: str, msg: str = "hello") -> dict:
    return {"timestamp": ts, "message": msg, "level": "info"}


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------

def test_default_granularity_is_day():
    p = LogPartitioner()
    assert p.granularity == "day"


def test_custom_granularity_stored():
    p = LogPartitioner(granularity="hour")
    assert p.granularity == "hour"


def test_invalid_granularity_raises():
    with pytest.raises(ValueError, match="granularity"):
        LogPartitioner(granularity="minute")


def test_default_ts_field_is_timestamp():
    p = LogPartitioner()
    assert p.ts_field == "timestamp"


def test_custom_ts_field_stored():
    p = LogPartitioner(ts_field="time")
    assert p.ts_field == "time"


def test_empty_ts_field_raises():
    with pytest.raises(ValueError, match="ts_field"):
        LogPartitioner(ts_field="")


def test_whitespace_ts_field_raises():
    with pytest.raises(ValueError, match="ts_field"):
        LogPartitioner(ts_field="   ")


# ---------------------------------------------------------------------------
# feed / buckets
# ---------------------------------------------------------------------------

def test_empty_feed_yields_no_buckets():
    p = LogPartitioner()
    p.feed([])
    assert p.buckets == {}


def test_single_entry_creates_one_bucket():
    p = LogPartitioner(granularity="day")
    p.feed([_e("2024-03-15T10:00:00")])
    assert "2024-03-15" in p.buckets


def test_two_entries_same_day_in_same_bucket():
    p = LogPartitioner(granularity="day")
    p.feed([_e("2024-03-15T08:00:00"), _e("2024-03-15T22:00:00")])
    assert len(p.buckets) == 1
    assert len(p.get("2024-03-15")) == 2


def test_entries_on_different_days_split():
    p = LogPartitioner(granularity="day")
    p.feed([_e("2024-03-15T08:00:00"), _e("2024-03-16T08:00:00")])
    assert "2024-03-15" in p.buckets
    assert "2024-03-16" in p.buckets


def test_hour_granularity_splits_by_hour():
    p = LogPartitioner(granularity="hour")
    p.feed([_e("2024-03-15T08:00:00"), _e("2024-03-15T09:00:00")])
    assert "2024-03-15T08" in p.buckets
    assert "2024-03-15T09" in p.buckets


def test_month_granularity():
    p = LogPartitioner(granularity="month")
    p.feed([_e("2024-03-15"), _e("2024-04-01")])
    assert "2024-03" in p.buckets
    assert "2024-04" in p.buckets


def test_year_granularity():
    p = LogPartitioner(granularity="year")
    p.feed([_e("2023-12-31"), _e("2024-01-01")])
    assert "2023" in p.buckets
    assert "2024" in p.buckets


def test_missing_timestamp_goes_to_unknown():
    p = LogPartitioner()
    p.feed([{"message": "no ts"}])
    assert "unknown" in p.buckets


def test_malformed_timestamp_goes_to_unknown():
    p = LogPartitioner()
    p.feed([_e("not-a-date")])
    assert "unknown" in p.buckets


# ---------------------------------------------------------------------------
# get / partition_keys / reset
# ---------------------------------------------------------------------------

def test_get_returns_empty_list_for_missing_key():
    p = LogPartitioner()
    assert p.get("2024-01-01") == []


def test_partition_keys_are_sorted():
    p = LogPartitioner(granularity="day")
    p.feed([_e("2024-03-17"), _e("2024-03-15"), _e("2024-03-16")])
    assert p.partition_keys == ["2024-03-15", "2024-03-16", "2024-03-17"]


def test_reset_clears_buckets():
    p = LogPartitioner()
    p.feed([_e("2024-03-15")])
    p.reset()
    assert p.buckets == {}


def test_reset_returns_self():
    p = LogPartitioner()
    assert p.reset() is p


def test_feed_returns_self():
    p = LogPartitioner()
    assert p.feed([]) is p


# ---------------------------------------------------------------------------
# Custom key function
# ---------------------------------------------------------------------------

def test_custom_key_fn_overrides_default():
    p = LogPartitioner(key_fn=lambda e: e.get("level", "unknown"))
    p.feed([{"level": "error"}, {"level": "info"}, {"level": "error"}])
    assert len(p.get("error")) == 2
    assert len(p.get("info")) == 1
