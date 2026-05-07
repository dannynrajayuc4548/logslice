"""Tests for logslice.pipeline.LogPipeline."""

import json
import os
import tempfile

import pytest

from logslice.filters import RegexFilter, TimeRangeFilter
from logslice.formatters import JSONFormatter, PlainFormatter
from logslice.pipeline import LogPipeline


SAMPLE_LINES = [
    '{"timestamp": "2024-01-01T10:00:00", "level": "INFO", "message": "startup"}',
    '{"timestamp": "2024-01-01T10:01:00", "level": "ERROR", "message": "disk full"}',
    '{"timestamp": "2024-01-01T10:02:00", "level": "INFO", "message": "shutdown"}',
    '{"timestamp": "2024-01-01T10:03:00", "level": "WARNING", "message": "low memory"}',
]


def _write_tmp(lines):
    fd, path = tempfile.mkstemp(suffix=".log")
    with os.fdopen(fd, "w") as fh:
        fh.write("\n".join(lines) + "\n")
    return path


# ---------------------------------------------------------------------------
# Basic pipeline behaviour
# ---------------------------------------------------------------------------

class TestLogPipeline:
    def test_no_filters_returns_all(self):
        pipeline = LogPipeline(formatter=PlainFormatter())
        results = pipeline.run(SAMPLE_LINES)
        assert len(results) == 4

    def test_regex_filter_reduces_results(self):
        pipeline = LogPipeline(formatter=PlainFormatter())
        pipeline.add_filter(RegexFilter("ERROR"))
        results = pipeline.run(SAMPLE_LINES)
        assert len(results) == 1
        assert "disk full" in results[0]

    def test_chaining_returns_self(self):
        pipeline = LogPipeline()
        ret = pipeline.add_filter(RegexFilter("x"))
        assert ret is pipeline

    def test_json_formatter_output_is_valid_json(self):
        pipeline = LogPipeline(formatter=JSONFormatter())
        pipeline.add_filter(RegexFilter("ERROR"))
        results = pipeline.run(SAMPLE_LINES)
        assert len(results) == 1
        obj = json.loads(results[0])
        assert obj["level"] == "ERROR"

    def test_set_formatter_replaces_formatter(self):
        pipeline = LogPipeline(formatter=PlainFormatter())
        pipeline.set_formatter(JSONFormatter())
        pipeline.add_filter(RegexFilter("startup"))
        results = pipeline.run(SAMPLE_LINES)
        assert len(results) == 1
        obj = json.loads(results[0])
        assert obj["message"] == "startup"

    def test_multiple_filters_are_anded(self):
        """Both filters must match — only entries passing all filters appear."""
        pipeline = LogPipeline(formatter=PlainFormatter())
        pipeline.add_filter(RegexFilter("INFO"))
        pipeline.add_filter(RegexFilter("startup"))
        results = pipeline.run(SAMPLE_LINES)
        assert len(results) == 1
        assert "startup" in results[0]

    def test_run_file_reads_from_disk(self):
        path = _write_tmp(SAMPLE_LINES)
        try:
            pipeline = LogPipeline(formatter=PlainFormatter())
            pipeline.add_filter(RegexFilter("WARNING"))
            results = pipeline.run_file(path)
            assert len(results) == 1
            assert "low memory" in results[0]
        finally:
            os.unlink(path)

    def test_empty_input_returns_empty_list(self):
        pipeline = LogPipeline()
        assert pipeline.run([]) == []

    def test_malformed_lines_are_skipped(self):
        lines = ["not json at all", SAMPLE_LINES[1]]
        pipeline = LogPipeline(formatter=PlainFormatter())
        results = pipeline.run(lines)
        # Only the valid JSON line should survive
        assert len(results) == 1
