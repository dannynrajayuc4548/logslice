"""Tests for LogReplayer."""

import time
from datetime import datetime

import pytest

from logslice.replayer import LogReplayer


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _entries(timestamps):
    """Build minimal log dicts with the given ISO timestamp strings."""
    return [{"timestamp": ts, "message": f"msg {i}"} for i, ts in enumerate(timestamps)]


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------

class TestConstruction:
    def test_default_speed_is_one(self):
        r = LogReplayer()
        assert r.speed == 1.0

    def test_custom_speed_stored(self):
        r = LogReplayer(speed=3.5)
        assert r.speed == 3.5

    def test_zero_speed_allowed(self):
        r = LogReplayer(speed=0.0)
        assert r.speed == 0.0

    def test_negative_speed_raises(self):
        with pytest.raises(ValueError, match="speed"):
            LogReplayer(speed=-1.0)

    def test_timestamp_field_stored(self):
        r = LogReplayer(timestamp_field="ts")
        assert r.timestamp_field == "ts"


# ---------------------------------------------------------------------------
# Collect / no delay (speed=0)
# ---------------------------------------------------------------------------

class TestCollect:
    def test_returns_all_entries(self):
        entries = _entries(["2024-01-01T00:00:00", "2024-01-01T00:00:01"])
        r = LogReplayer(speed=0)
        result = r.collect(entries)
        assert len(result) == 2

    def test_entries_unchanged(self):
        entries = _entries(["2024-01-01T00:00:00"])
        r = LogReplayer(speed=0)
        result = r.collect(entries)
        assert result[0]["message"] == "msg 0"

    def test_missing_timestamp_still_yields(self):
        entries = [{"message": "no ts"}]
        r = LogReplayer(speed=0)
        result = r.collect(entries)
        assert result == entries

    def test_unparseable_timestamp_still_yields(self):
        entries = [{"timestamp": "not-a-date", "message": "bad"}]
        r = LogReplayer(speed=0)
        result = r.collect(entries)
        assert len(result) == 1

    def test_empty_input_returns_empty(self):
        r = LogReplayer(speed=0)
        assert r.collect([]) == []


# ---------------------------------------------------------------------------
# on_entry callback
# ---------------------------------------------------------------------------

class TestCallback:
    def test_callback_invoked_for_each_entry(self):
        seen = []
        r = LogReplayer(speed=0, on_entry=lambda e: seen.append(e["message"]))
        entries = _entries(["2024-01-01T00:00:00", "2024-01-01T00:00:01"])
        r.collect(entries)
        assert seen == ["msg 0", "msg 1"]

    def test_no_callback_is_fine(self):
        r = LogReplayer(speed=0, on_entry=None)
        entries = _entries(["2024-01-01T00:00:00"])
        assert len(r.collect(entries)) == 1


# ---------------------------------------------------------------------------
# Timing (very fast speed to keep tests quick)
# ---------------------------------------------------------------------------

class TestTiming:
    def test_high_speed_finishes_quickly(self):
        # Two entries 1 second apart replayed at 1000x speed → ~1 ms delay
        entries = _entries(["2024-01-01T00:00:00", "2024-01-01T00:00:01"])
        r = LogReplayer(speed=1000.0)
        start = time.monotonic()
        r.collect(entries)
        elapsed = time.monotonic() - start
        assert elapsed < 0.5  # generous upper bound

    def test_zero_speed_no_sleep(self):
        entries = _entries(["2024-01-01T00:00:00"] * 50)
        r = LogReplayer(speed=0)
        start = time.monotonic()
        r.collect(entries)
        assert time.monotonic() - start < 0.2
