"""Tests for ClassifyPipeline."""
import json
import os
import tempfile

import pytest

from logslice.classify_pipeline import ClassifyPipeline
from logslice.pipeline import LogPipeline
from logslice.classifier import LogClassifier
from logslice.filters import RegexFilter


def _write_log(lines):
    f = tempfile.NamedTemporaryFile(
        mode="w", suffix=".jsonl", delete=False
    )
    for line in lines:
        f.write(json.dumps(line) + "\n")
    f.close()
    return f.name


@pytest.fixture()
def log_path():
    path = _write_log([
        {"level": "ERROR", "message": "disk full"},
        {"level": "WARN",  "message": "high memory"},
        {"level": "INFO",  "message": "started"},
    ])
    yield path
    os.unlink(path)


# ------------------------------------------------------------------
# Construction
# ------------------------------------------------------------------

def test_pipeline_attribute_is_log_pipeline(log_path):
    cp = ClassifyPipeline(log_path)
    assert isinstance(cp.pipeline, LogPipeline)


def test_classifier_attribute_is_log_classifier(log_path):
    cp = ClassifyPipeline(log_path)
    assert isinstance(cp.classifier, LogClassifier)


def test_custom_category_field_forwarded(log_path):
    cp = ClassifyPipeline(log_path, category_field="kind")
    assert cp.classifier.category_field == "kind"


def test_custom_default_forwarded(log_path):
    cp = ClassifyPipeline(log_path, default="other")
    assert cp.classifier.default == "other"


# ------------------------------------------------------------------
# Builder returns self
# ------------------------------------------------------------------

def test_add_filter_returns_self(log_path):
    cp = ClassifyPipeline(log_path)
    assert cp.add_filter(RegexFilter("ERROR")) is cp


def test_add_rule_returns_self(log_path):
    cp = ClassifyPipeline(log_path)
    assert cp.add_rule("x", lambda e: True) is cp


# ------------------------------------------------------------------
# run / collect
# ------------------------------------------------------------------

def test_collect_returns_list(log_path):
    result = ClassifyPipeline(log_path).collect()
    assert isinstance(result, list)


def test_all_entries_have_category_field(log_path):
    result = ClassifyPipeline(log_path).collect()
    assert all("category" in e for e in result)


def test_rule_applied_to_matching_entries(log_path):
    cp = ClassifyPipeline(log_path)
    cp.add_rule("error", lambda e: e.get("level") == "ERROR")
    result = cp.collect()
    errors = [e for e in result if e["level"] == "ERROR"]
    assert all(e["category"] == "error" for e in errors)


def test_unmatched_entries_get_default(log_path):
    cp = ClassifyPipeline(log_path)
    cp.add_rule("error", lambda e: e.get("level") == "ERROR")
    result = cp.collect()
    non_errors = [e for e in result if e["level"] != "ERROR"]
    assert all(e["category"] == "uncategorized" for e in non_errors)


def test_filter_reduces_entries_before_classification(log_path):
    cp = ClassifyPipeline(log_path)
    cp.add_filter(RegexFilter("ERROR"))
    cp.add_rule("error", lambda e: e.get("level") == "ERROR")
    result = cp.collect()
    assert len(result) == 1
    assert result[0]["category"] == "error"
