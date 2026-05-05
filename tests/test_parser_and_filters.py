"""Tests for LogParser, RegexFilter, and TimeRangeFilter."""

import json
import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from logslice import LogParser, RegexFilter, TimeRangeFilter


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write_log(lines: list[dict | str]) -> Path:
    """Write log lines to a temp file and return its path."""
    tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False)
    for line in lines:
        tmp.write((json.dumps(line) if isinstance(line, dict) else line) + "\n")
    tmp.close()
    return Path(tmp.name)


SAMPLE_RECORDS = [
    {"timestamp": "2024-01-10T08:00:00", "level": "INFO",  "message": "Server started"},
    {"timestamp": "2024-01-10T08:05:00", "level": "ERROR", "message": "Disk full"},
    {"timestamp": "2024-01-10T08:10:00", "level": "INFO",  "message": "Request received"},
    {"timestamp": "2024-01-10T08:15:00", "level": "WARN",  "message": "High memory usage"},
]


# ---------------------------------------------------------------------------
# RegexFilter tests
# ---------------------------------------------------------------------------

class TestRegexFilter:
    def test_matches_substring(self):
        f = RegexFilter(r"Disk")
        assert f.match({"message": "Disk full"})
        assert not f.match({"message": "All good"})

    def test_custom_field(self):
        f = RegexFilter(r"ERROR", field="level")
        assert f.match({"level": "ERROR", "message": "oops"})
        assert not f.match({"level": "INFO", "message": "oops"})

    def test_case_insensitive_flag(self):
        import re
        f = RegexFilter(r"disk", flags=re.IGNORECASE)
        assert f.match({"message": "Disk full"})

    def test_missing_field_returns_false(self):
        f = RegexFilter(r"anything", field="nonexistent")
        assert not f.match({"message": "hello"})


# ---------------------------------------------------------------------------
# TimeRangeFilter tests
# ---------------------------------------------------------------------------

class TestTimeRangeFilter:
    def test_within_range(self):
        f = TimeRangeFilter(
            start=datetime(2024, 1, 10, 8, 0, 0),
            end=datetime(2024, 1, 10, 8, 10, 0),
        )
        assert f.match({"timestamp": "2024-01-10T08:05:00"})

    def test_outside_range(self):
        f = TimeRangeFilter(
            start=datetime(2024, 1, 10, 9, 0, 0),
            end=datetime(2024, 1, 10, 10, 0, 0),
        )
        assert not f.match({"timestamp": "2024-01-10T08:05:00"})

    def test_open_end_boundary(self):
        f = TimeRangeFilter(start=datetime(2024, 1, 10, 8, 0, 0))
        assert f.match({"timestamp": "2024-01-10T23:59:59"})

    def test_missing_timestamp_returns_false(self):
        f = TimeRangeFilter(start=datetime(2024, 1, 10, 8, 0, 0))
        assert not f.match({"message": "no timestamp here"})

    def test_raises_without_bounds(self):
        with pytest.raises(ValueError):
            TimeRangeFilter()


# ---------------------------------------------------------------------------
# LogParser integration tests
# ---------------------------------------------------------------------------

class TestLogParser:
    def test_stream_all_records(self):
        path = _write_log(SAMPLE_RECORDS)
        parser = LogParser(path)
        assert parser.count() == len(SAMPLE_RECORDS)

    def test_regex_filter_integration(self):
        path = _write_log(SAMPLE_RECORDS)
        parser = LogParser(path, filters=[RegexFilter(r"ERROR", field="level")])
        results = parser.to_list()
        assert len(results) == 1
        assert results[0]["message"] == "Disk full"

    def test_time_range_filter_integration(self):
        path = _write_log(SAMPLE_RECORDS)
        f = TimeRangeFilter(
            start=datetime(2024, 1, 10, 8, 5, 0),
            end=datetime(2024, 1, 10, 8, 10, 0),
        )
        results = LogParser(path, filters=[f]).to_list()
        assert len(results) == 2

    def test_combined_filters(self):
        path = _write_log(SAMPLE_RECORDS)
        parser = (
            LogParser(path)
            .add_filter(TimeRangeFilter(start=datetime(2024, 1, 10, 8, 0, 0)))
            .add_filter(RegexFilter(r"memory", flags=__import__("re").IGNORECASE))
        )
        results = parser.to_list()
        assert len(results) == 1
        assert "memory" in results[0]["message"].lower()

    def test_plain_text_fallback(self):
        path = _write_log(["plain text line", "another plain line"])
        parser = LogParser(path)
        records = parser.to_list()
        assert all(r.get("_raw") for r in records)
        assert records[0]["message"] == "plain text line"
