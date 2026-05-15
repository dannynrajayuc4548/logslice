"""Tests for HighlightPipeline."""
import json
import re
import tempfile
import os
import pytest

from logslice.highlight_pipeline import HighlightPipeline
from logslice.pipeline import LogPipeline
from logslice.highlighter import LogHighlighter


def _write_log(entries):
    f = tempfile.NamedTemporaryFile(
        mode="w", suffix=".jsonl", delete=False
    )
    for e in entries:
        f.write(json.dumps(e) + "\n")
    f.close()
    return f.name


@pytest.fixture()
def log_path():
    entries = [
        {"timestamp": "2024-01-01T00:00:00", "level": "ERROR", "message": "disk full"},
        {"timestamp": "2024-01-01T00:01:00", "level": "INFO",  "message": "all ok"},
        {"timestamp": "2024-01-01T00:02:00", "level": "ERROR", "message": "timeout"},
    ]
    path = _write_log(entries)
    yield path
    os.unlink(path)


def test_pipeline_attribute_is_log_pipeline(log_path):
    hp = HighlightPipeline(log_path)
    assert isinstance(hp.pipeline, LogPipeline)


def test_highlighter_attribute_is_log_highlighter(log_path):
    hp = HighlightPipeline(log_path)
    assert isinstance(hp.highlighter, LogHighlighter)


def test_custom_highlight_key_forwarded(log_path):
    hp = HighlightPipeline(log_path, highlight_key="_marks")
    assert hp.highlighter.highlight_key == "_marks"


def test_add_rule_returns_self(log_path):
    hp = HighlightPipeline(log_path)
    assert hp.add_rule("message", r"error") is hp


def test_add_filter_returns_self(log_path):
    from logslice.filters import RegexFilter
    hp = HighlightPipeline(log_path)
    assert hp.add_filter(RegexFilter(r"ERROR", field="level")) is hp


def test_enrich_returns_self(log_path):
    hp = HighlightPipeline(log_path)
    assert hp.enrich("env", "prod") is hp


def test_run_returns_all_entries_when_no_filter(log_path):
    hp = HighlightPipeline(log_path)
    results = hp.run()
    assert len(results) == 3


def test_run_annotates_matching_entries(log_path):
    hp = HighlightPipeline(log_path)
    hp.add_rule("level", r"ERROR")
    results = hp.run()
    highlighted = [r for r in results if "_highlights" in r]
    assert len(highlighted) == 2


def test_non_matching_entries_have_no_highlight_key(log_path):
    hp = HighlightPipeline(log_path)
    hp.add_rule("level", r"ERROR")
    results = hp.run()
    plain = [r for r in results if "_highlights" not in r]
    assert len(plain) == 1
    assert plain[0]["level"] == "INFO"


def test_highlight_key_content(log_path):
    hp = HighlightPipeline(log_path)
    hp.add_rule("message", r"timeout")
    results = hp.run()
    hit = next(r for r in results if "_highlights" in r)
    assert hit["_highlights"][0]["match"] == "timeout"
    assert hit["_highlights"][0]["field"] == "message"
