"""Tests for logslice.group_pipeline.GroupPipeline."""
import json
import tempfile
import os
import pytest

from logslice.group_pipeline import GroupPipeline
from logslice.pipeline import LogPipeline
from logslice.grouper import LogGrouper
from logslice.filters import RegexFilter


def _write_log(entries):
    tmp = tempfile.NamedTemporaryFile(
        mode="w", suffix=".jsonl", delete=False
    )
    for e in entries:
        tmp.write(json.dumps(e) + "\n")
    tmp.flush()
    tmp.close()
    return tmp.name


@pytest.fixture()
def log_path():
    path = _write_log([
        {"level": "info",  "message": "started"},
        {"level": "error", "message": "boom"},
        {"level": "info",  "message": "done"},
        {"level": "warn",  "message": "slow"},
        {"level": "error", "message": "crash"},
    ])
    yield path
    os.unlink(path)


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------

def test_pipeline_attribute_is_log_pipeline(log_path):
    gp = GroupPipeline(log_path)
    assert isinstance(gp.pipeline, LogPipeline)


def test_grouper_attribute_is_log_grouper(log_path):
    gp = GroupPipeline(log_path)
    assert isinstance(gp.grouper, LogGrouper)


def test_custom_field_forwarded(log_path):
    gp = GroupPipeline(log_path, field="message")
    assert gp.grouper.field == "message"


def test_custom_default_forwarded(log_path):
    gp = GroupPipeline(log_path, default="misc")
    assert gp.grouper.default == "misc"


# ---------------------------------------------------------------------------
# run()
# ---------------------------------------------------------------------------

def test_run_returns_all_buckets(log_path):
    gp = GroupPipeline(log_path)
    buckets = gp.run()
    assert set(buckets.keys()) == {"info", "error", "warn"}


def test_run_correct_counts(log_path):
    gp = GroupPipeline(log_path)
    buckets = gp.run()
    assert len(buckets["info"]) == 2
    assert len(buckets["error"]) == 2
    assert len(buckets["warn"]) == 1


def test_run_clears_previous_state(log_path):
    gp = GroupPipeline(log_path)
    gp.run()
    buckets = gp.run()  # second run should not double-count
    assert len(buckets["info"]) == 2


# ---------------------------------------------------------------------------
# counts()
# ---------------------------------------------------------------------------

def test_counts_returns_int_per_bucket(log_path):
    gp = GroupPipeline(log_path)
    c = gp.counts()
    assert c["info"] == 2
    assert c["error"] == 2


# ---------------------------------------------------------------------------
# add_filter delegation
# ---------------------------------------------------------------------------

def test_add_filter_reduces_results(log_path):
    gp = GroupPipeline(log_path)
    gp.add_filter(RegexFilter("boom"))
    buckets = gp.run()
    assert buckets.get("error", []) == [{"level": "error", "message": "boom"}]
    assert "info" not in buckets


def test_add_filter_returns_self(log_path):
    gp = GroupPipeline(log_path)
    assert gp.add_filter(RegexFilter("x")) is gp


# ---------------------------------------------------------------------------
# on_group delegation
# ---------------------------------------------------------------------------

def test_on_group_hook_fires(log_path):
    gp = GroupPipeline(log_path)
    seen = []
    gp.on_group("error", seen.append)
    gp.run()
    assert len(seen) == 2


def test_on_group_returns_self(log_path):
    gp = GroupPipeline(log_path)
    assert gp.on_group("info", lambda e: None) is gp
