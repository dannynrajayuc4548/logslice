"""Tests for logslice.formatters and logslice.writer."""

import io
import json
import os
import tempfile

import pytest

from logslice.formatters import JSONFormatter, PlainFormatter, CSVFormatter
from logslice.parser import LogParser
from logslice.writer import LogWriter


SAMPLE_ENTRY = {"level": "ERROR", "msg": "disk full", "host": "web-01"}


# ---------------------------------------------------------------------------
# JSONFormatter
# ---------------------------------------------------------------------------

class TestJSONFormatter:
    def test_round_trip(self):
        fmt = JSONFormatter()
        result = json.loads(fmt.format(SAMPLE_ENTRY))
        assert result == SAMPLE_ENTRY

    def test_sorted_keys(self):
        fmt = JSONFormatter(sort_keys=True)
        text = fmt.format(SAMPLE_ENTRY)
        keys = list(json.loads(text).keys())
        assert keys == sorted(keys)

    def test_indent_produces_multiline(self):
        fmt = JSONFormatter(indent=2)
        assert "\n" in fmt.format(SAMPLE_ENTRY)


# ---------------------------------------------------------------------------
# PlainFormatter
# ---------------------------------------------------------------------------

class TestPlainFormatter:
    def test_default_includes_all_fields(self):
        fmt = PlainFormatter()
        result = fmt.format(SAMPLE_ENTRY)
        for k, v in SAMPLE_ENTRY.items():
            assert f"{k}={v}" in result

    def test_custom_fields_order(self):
        fmt = PlainFormatter(fields=["host", "level"], separator=",")
        result = fmt.format(SAMPLE_ENTRY)
        assert result == "host=web-01,level=ERROR"

    def test_missing_field_skipped(self):
        fmt = PlainFormatter(fields=["level", "nonexistent"])
        result = fmt.format(SAMPLE_ENTRY)
        assert "nonexistent" not in result
        assert "level=ERROR" in result


# ---------------------------------------------------------------------------
# CSVFormatter
# ---------------------------------------------------------------------------

class TestCSVFormatter:
    def test_basic_csv(self):
        fmt = CSVFormatter(fields=["level", "msg", "host"])
        assert fmt.format(SAMPLE_ENTRY) == "ERROR,disk full,web-01"

    def test_value_with_comma_is_quoted(self):
        entry = {"msg": "a,b"}
        fmt = CSVFormatter(fields=["msg"])
        assert fmt.format(entry) == '"a,b"'

    def test_missing_field_is_empty_string(self):
        fmt = CSVFormatter(fields=["level", "missing"])
        result = fmt.format(SAMPLE_ENTRY)
        assert result == "ERROR,"


# ---------------------------------------------------------------------------
# LogWriter integration
# ---------------------------------------------------------------------------

def _write_log(path, lines):
    with open(path, "w") as f:
        for line in lines:
            f.write(json.dumps(line) + "\n")


class TestLogWriter:
    def test_write_returns_count(self, tmp_path):
        log = tmp_path / "app.log"
        entries = [
            {"level": "INFO", "msg": "start"},
            {"level": "ERROR", "msg": "fail"},
        ]
        _write_log(str(log), entries)
        sink = io.StringIO()
        parser = LogParser()
        writer = LogWriter(parser, formatter=JSONFormatter(), sink=sink)
        count = writer.write(str(log))
        assert count == 2
        lines = sink.getvalue().strip().splitlines()
        assert len(lines) == 2

    def test_collect_yields_formatted_strings(self, tmp_path):
        log = tmp_path / "app.log"
        _write_log(str(log), [{"level": "WARN", "msg": "low memory"}])
        parser = LogParser()
        writer = LogWriter(parser, formatter=PlainFormatter(separator="|"))
        results = list(writer.collect(str(log)))
        assert len(results) == 1
        assert "level=WARN" in results[0]
