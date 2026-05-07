"""Tests for logslice.exporter.LogExporter."""

import io
import json
import os
import tempfile
import pytest

from logslice.exporter import LogExporter
from logslice.formatters import JSONFormatter, PlainFormatter


SAMPLE_ENTRIES = [
    {"level": "INFO", "message": "started", "ts": "2024-01-01T00:00:00"},
    {"level": "ERROR", "message": "failed", "ts": "2024-01-01T00:01:00"},
    {"level": "DEBUG", "message": "done", "ts": "2024-01-01T00:02:00"},
]


class TestToStream:
    def test_returns_correct_count(self):
        exporter = LogExporter()
        buf = io.StringIO()
        count = exporter.to_stream(SAMPLE_ENTRIES, buf)
        assert count == 3

    def test_each_entry_on_own_line(self):
        exporter = LogExporter()
        buf = io.StringIO()
        exporter.to_stream(SAMPLE_ENTRIES, buf)
        lines = buf.getvalue().splitlines()
        assert len(lines) == 3

    def test_uses_formatter_when_provided(self):
        exporter = LogExporter(formatter=JSONFormatter())
        buf = io.StringIO()
        exporter.to_stream(SAMPLE_ENTRIES[:1], buf)
        line = buf.getvalue().strip()
        parsed = json.loads(line)
        assert parsed["level"] == "INFO"

    def test_plain_formatter(self):
        exporter = LogExporter(formatter=PlainFormatter())
        buf = io.StringIO()
        exporter.to_stream(SAMPLE_ENTRIES[:1], buf)
        line = buf.getvalue().strip()
        assert "INFO" in line
        assert "started" in line

    def test_empty_entries_returns_zero(self):
        exporter = LogExporter()
        buf = io.StringIO()
        count = exporter.to_stream([], buf)
        assert count == 0
        assert buf.getvalue() == ""


class TestToFile:
    def test_writes_to_file(self):
        exporter = LogExporter(formatter=JSONFormatter())
        with tempfile.NamedTemporaryFile(mode="r", suffix=".log", delete=False) as f:
            path = f.name
        try:
            count = exporter.to_file(SAMPLE_ENTRIES, path)
            assert count == 3
            with open(path, encoding="utf-8") as fh:
                lines = fh.read().splitlines()
            assert len(lines) == 3
        finally:
            os.unlink(path)

    def test_append_mode(self):
        exporter = LogExporter()
        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            path = f.name
        try:
            exporter.to_file(SAMPLE_ENTRIES[:1], path, mode="w")
            exporter.to_file(SAMPLE_ENTRIES[1:2], path, mode="a")
            with open(path, encoding="utf-8") as fh:
                lines = fh.read().splitlines()
            assert len(lines) == 2
        finally:
            os.unlink(path)


class TestToJsonl:
    def test_valid_jsonl_output(self):
        exporter = LogExporter()
        with tempfile.NamedTemporaryFile(mode="r", suffix=".jsonl", delete=False) as f:
            path = f.name
        try:
            count = exporter.to_jsonl(SAMPLE_ENTRIES, path)
            assert count == 3
            with open(path, encoding="utf-8") as fh:
                lines = fh.read().splitlines()
            assert len(lines) == 3
            for line in lines:
                obj = json.loads(line)
                assert "level" in obj
        finally:
            os.unlink(path)
