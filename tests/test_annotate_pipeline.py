"""Tests for AnnotatePipeline."""
import json
import tempfile
import os

import pytest

from logslice.annotate_pipeline import AnnotatePipeline
from logslice.annotator import LogAnnotator
from logslice.filters import RegexFilter
from logslice.pipeline import LogPipeline


def _write_log(entries):
    tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False)
    for e in entries:
        tmp.write(json.dumps(e) + "\n")
    tmp.close()
    return tmp.name


@pytest.fixture
def log_path():
    path = _write_log([
        {"timestamp": "2024-01-01T00:00:00", "level": "INFO", "message": "started"},
        {"timestamp": "2024-01-01T00:01:00", "level": "ERROR", "message": "boom"},
        {"timestamp": "2024-01-01T00:02:00", "level": "WARNING", "message": "slow"},
    ])
    yield path
    os.unlink(path)


def test_pipeline_attribute_is_log_pipeline(log_path):
    ap = AnnotatePipeline(log_path)
    assert isinstance(ap.pipeline, LogPipeline)


def test_annotator_attribute_is_log_annotator(log_path):
    ap = AnnotatePipeline(log_path)
    assert isinstance(ap.annotator, LogAnnotator)


def test_custom_annotation_key_forwarded(log_path):
    ap = AnnotatePipeline(log_path, annotation_key="meta")
    assert ap.annotator.annotation_key == "meta"


def test_add_filter_returns_self(log_path):
    ap = AnnotatePipeline(log_path)
    result = ap.add_filter(RegexFilter("boom"))
    assert result is ap


def test_add_annotation_returns_self(log_path):
    ap = AnnotatePipeline(log_path)
    result = ap.add_annotation(lambda e: True, "flag", True)
    assert result is ap


def test_collect_returns_list(log_path):
    ap = AnnotatePipeline(log_path)
    results = ap.collect()
    assert isinstance(results, list)


def test_no_filter_returns_all_entries(log_path):
    ap = AnnotatePipeline(log_path)
    results = ap.collect()
    assert len(results) == 3


def test_filter_reduces_entries(log_path):
    ap = AnnotatePipeline(log_path)
    ap.add_filter(RegexFilter("ERROR", field="level"))
    results = ap.collect()
    assert len(results) == 1
    assert results[0]["level"] == "ERROR"


def test_annotation_applied_to_all_entries(log_path):
    ap = AnnotatePipeline(log_path)
    ap.add_annotation(lambda e: True, "processed", True)
    results = ap.collect()
    assert all(r["annotations"]["processed"] is True for r in results)


def test_annotation_applied_selectively(log_path):
    ap = AnnotatePipeline(log_path)
    ap.add_annotation(lambda e: e.get("level") == "ERROR", "critical", True)
    results = ap.collect()
    error_entries = [r for r in results if r["level"] == "ERROR"]
    non_error = [r for r in results if r["level"] != "ERROR"]
    assert all(r["annotations"].get("critical") is True for r in error_entries)
    assert all("critical" not in r["annotations"] for r in non_error)


def test_stream_is_iterator(log_path):
    ap = AnnotatePipeline(log_path)
    import types
    assert isinstance(ap.stream(), types.GeneratorType)


def test_chaining(log_path):
    results = (
        AnnotatePipeline(log_path)
        .add_filter(RegexFilter("boom"))
        .add_annotation(lambda e: True, "matched", True)
        .collect()
    )
    assert len(results) == 1
    assert results[0]["annotations"]["matched"] is True
