"""Tests for logslice.formatter_pipeline.FormatterPipeline."""

from __future__ import annotations

import json
import os
import tempfile
from typing import List

import pytest

from logslice.formatter_pipeline import FormatterPipeline
from logslice.formatters import JSONFormatter, PlainFormatter
from logslice.filters import RegexFilter


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write_log(entries: List[dict]) -> str:
    tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False)
    for e in entries:
        tmp.write(json.dumps(e) + "\n")
    tmp.close()
    return tmp.name


SAMPLE = [
    {"level": "INFO",  "message": "server started"},
    {"level": "ERROR", "message": "disk full"},
    {"level": "INFO",  "message": "request handled"},
    {"level": "WARN",  "message": "slow query"},
]


@pytest.fixture()
def log_path():
    path = _write_log(SAMPLE)
    yield path
    os.unlink(path)


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------

def test_pipeline_attribute_is_log_pipeline(log_path):
    from logslice.pipeline import LogPipeline
    fp = FormatterPipeline(log_path)
    assert isinstance(fp.pipeline, LogPipeline)


def test_default_formatter_is_json(log_path):
    fp = FormatterPipeline(log_path)
    assert isinstance(fp.formatter, JSONFormatter)


def test_custom_formatter_stored(log_path):
    plain = PlainFormatter()
    fp = FormatterPipeline(log_path, formatter=plain)
    assert fp.formatter is plain


# ---------------------------------------------------------------------------
# set_formatter
# ---------------------------------------------------------------------------

def test_set_formatter_returns_self(log_path):
    fp = FormatterPipeline(log_path)
    result = fp.set_formatter(PlainFormatter())
    assert result is fp


def test_set_formatter_updates_formatter(log_path):
    fp = FormatterPipeline(log_path)
    plain = PlainFormatter()
    fp.set_formatter(plain)
    assert fp.formatter is plain


def test_set_formatter_raises_on_non_formatter(log_path):
    fp = FormatterPipeline(log_path)
    with pytest.raises(TypeError):
        fp.set_formatter("not-a-formatter")  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# add_filter
# ---------------------------------------------------------------------------

def test_add_filter_returns_self(log_path):
    fp = FormatterPipeline(log_path)
    result = fp.add_filter(RegexFilter("INFO"))
    assert result is fp


def test_add_filter_reduces_results(log_path):
    fp = FormatterPipeline(log_path)
    fp.add_filter(RegexFilter("ERROR"))
    lines = fp.render()
    assert len(lines) == 1
    assert "disk full" in lines[0]


# ---------------------------------------------------------------------------
# render
# ---------------------------------------------------------------------------

def test_render_returns_list_of_strings(log_path):
    fp = FormatterPipeline(log_path)
    lines = fp.render()
    assert isinstance(lines, list)
    assert all(isinstance(l, str) for l in lines)


def test_render_count_matches_unfiltered_entries(log_path):
    fp = FormatterPipeline(log_path)
    assert len(fp.render()) == len(SAMPLE)


def test_render_json_is_parseable(log_path):
    fp = FormatterPipeline(log_path)
    for line in fp.render():
        parsed = json.loads(line)
        assert "level" in parsed


def test_render_with_plain_formatter(log_path):
    fp = FormatterPipeline(log_path, formatter=PlainFormatter())
    lines = fp.render()
    # PlainFormatter should produce non-empty strings
    assert all(len(l) > 0 for l in lines)


# ---------------------------------------------------------------------------
# stream_rendered
# ---------------------------------------------------------------------------

def test_stream_rendered_yields_strings(log_path):
    fp = FormatterPipeline(log_path)
    for item in fp.stream_rendered():
        assert isinstance(item, str)


def test_stream_rendered_count(log_path):
    fp = FormatterPipeline(log_path)
    assert sum(1 for _ in fp.stream_rendered()) == len(SAMPLE)
