"""Tests for AlertPipeline."""

import json
import tempfile
import os

import pytest

from logslice.alert_pipeline import AlertPipeline
from logslice.alerter import LogAlerter
from logslice.pipeline import LogPipeline


def _write_log(lines):
    tf = tempfile.NamedTemporaryFile(
        mode="w", suffix=".jsonl", delete=False
    )
    for line in lines:
        tf.write(json.dumps(line) + "\n")
    tf.flush()
    tf.close()
    return tf.name


@pytest.fixture()
def log_path():
    path = _write_log([
        {"level": "INFO", "message": "ok"},
        {"level": "ERROR", "message": "fail"},
        {"level": "ERROR", "message": "fail again"},
        {"level": "DEBUG", "message": "verbose"},
    ])
    yield path
    os.unlink(path)


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------

def test_pipeline_attribute_is_log_pipeline(log_path):
    ap = AlertPipeline(log_path)
    assert isinstance(ap.pipeline, LogPipeline)


def test_alerter_attribute_is_log_alerter(log_path):
    ap = AlertPipeline(log_path)
    assert isinstance(ap.alerter, LogAlerter)


# ---------------------------------------------------------------------------
# Chaining
# ---------------------------------------------------------------------------

def test_add_alert_returns_self(log_path):
    ap = AlertPipeline(log_path)
    result = ap.add_alert("r", lambda e: True, lambda n, e: None)
    assert result is ap


def test_add_filter_returns_self(log_path):
    from logslice.filters import RegexFilter
    ap = AlertPipeline(log_path)
    result = ap.add_filter(RegexFilter("ERROR"))
    assert result is ap


# ---------------------------------------------------------------------------
# run()
# ---------------------------------------------------------------------------

def test_run_returns_triggered_list(log_path):
    ap = AlertPipeline(log_path)
    ap.add_alert(
        "errors",
        condition=lambda e: e.get("level") == "ERROR",
        callback=lambda n, e: None,
    )
    triggered = ap.run()
    assert len(triggered) == 2


def test_run_no_alerts_returns_empty(log_path):
    ap = AlertPipeline(log_path)
    assert ap.run() == []


def test_pipeline_filter_reduces_alert_scope(log_path):
    """Only entries passing the pipeline filter are evaluated."""
    from logslice.filters import RegexFilter
    fired = []
    ap = AlertPipeline(log_path)
    ap.add_filter(RegexFilter("INFO"))
    ap.add_alert("all", lambda e: True, lambda n, e: fired.append(e))
    ap.run()
    # Only the INFO entry passes the regex filter
    assert len(fired) == 1
    assert fired[0]["level"] == "INFO"


def test_triggered_records_contain_rule_and_entry(log_path):
    ap = AlertPipeline(log_path)
    ap.add_alert("catch", lambda e: e.get("level") == "DEBUG", lambda n, e: None)
    triggered = ap.run()
    assert triggered[0]["rule"] == "catch"
    assert triggered[0]["entry"]["level"] == "DEBUG"
