"""Tests for logslice.tag_pipeline."""
import json
import tempfile
import os
import pytest

from logslice.tag_pipeline import TagPipeline
from logslice.pipeline import LogPipeline
from logslice.tagger import LogTagger
from logslice.filters import RegexFilter


def _write_log(lines):
    f = tempfile.NamedTemporaryFile(
        mode="w", suffix=".jsonl", delete=False
    )
    for line in lines:
        f.write(json.dumps(line) + "\n")
    f.flush()
    f.close()
    return f.name


@pytest.fixture()
def log_path():
    entries = [
        {"level": "INFO", "message": "started", "service": "api"},
        {"level": "ERROR", "message": "timeout reached", "service": "api"},
        {"level": "WARN", "message": "high memory", "service": "worker"},
        {"level": "ERROR", "message": "disk full", "service": "worker"},
    ]
    path = _write_log(entries)
    yield path
    os.unlink(path)


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------

def test_pipeline_attribute_is_log_pipeline(log_path):
    tp = TagPipeline(log_path)
    assert isinstance(tp.pipeline, LogPipeline)


def test_tagger_attribute_is_log_tagger(log_path):
    tp = TagPipeline(log_path)
    assert isinstance(tp.tagger, LogTagger)


def test_custom_tag_field_forwarded(log_path):
    tp = TagPipeline(log_path, tag_field="labels")
    assert tp.tagger.tag_field == "labels"


# ---------------------------------------------------------------------------
# Chaining
# ---------------------------------------------------------------------------

def test_tag_if_matches_returns_self(log_path):
    tp = TagPipeline(log_path)
    result = tp.tag_if_matches("t", "message", r"x")
    assert result is tp


def test_tag_if_field_equals_returns_self(log_path):
    tp = TagPipeline(log_path)
    result = tp.tag_if_field_equals("t", "level", "INFO")
    assert result is tp


def test_add_filter_returns_self(log_path):
    tp = TagPipeline(log_path)
    result = tp.add_filter(RegexFilter(r"ERROR"))
    assert result is tp


def test_add_rule_returns_self(log_path):
    tp = TagPipeline(log_path)
    result = tp.add_rule("x", lambda e: True)
    assert result is tp


# ---------------------------------------------------------------------------
# stream / collect
# ---------------------------------------------------------------------------

def test_collect_returns_all_entries_without_filters(log_path):
    tp = TagPipeline(log_path)
    results = tp.collect()
    assert len(results) == 4


def test_tags_field_present_on_all_entries(log_path):
    tp = TagPipeline(log_path)
    for entry in tp.stream():
        assert "tags" in entry


def test_tag_applied_to_matching_entries(log_path):
    tp = TagPipeline(log_path)
    tp.tag_if_field_equals("err", "level", "ERROR")
    results = tp.collect()
    tagged = [r for r in results if "err" in r["tags"]]
    assert len(tagged) == 2


def test_filter_reduces_before_tagging(log_path):
    tp = TagPipeline(log_path)
    tp.add_filter(RegexFilter(r"ERROR"))
    tp.tag_if_matches("timeout", "message", r"timeout")
    results = tp.collect()
    assert len(results) == 2
    timeout_tagged = [r for r in results if "timeout" in r["tags"]]
    assert len(timeout_tagged) == 1


def test_custom_tag_field_used_in_output(log_path):
    tp = TagPipeline(log_path, tag_field="labels")
    tp.add_rule("always", lambda e: True)
    for entry in tp.stream():
        assert "always" in entry["labels"]


def test_no_rules_produces_empty_tags(log_path):
    tp = TagPipeline(log_path)
    for entry in tp.collect():
        assert entry["tags"] == []


def test_multiple_tags_on_single_entry(log_path):
    tp = TagPipeline(log_path)
    tp.tag_if_field_equals("err", "level", "ERROR")
    tp.tag_if_matches("timeout", "message", r"timeout")
    results = {r["message"]: r["tags"] for r in tp.collect()}
    assert set(results["timeout reached"]) == {"err", "timeout"}
