"""Tests for ReplayPipeline."""

import json
import os
import tempfile

import pytest

from logslice.filters import RegexFilter
from logslice.replay_pipeline import ReplayPipeline
from logslice.replayer import LogReplayer
from logslice.pipeline import LogPipeline


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write_log(lines):
    """Write JSON-lines to a temp file and return its path."""
    f = tempfile.NamedTemporaryFile(
        mode="w", suffix=".jsonl", delete=False
    )
    for line in lines:
        f.write(json.dumps(line) + "\n")
    f.close()
    return f.name


LOG_ENTRIES = [
    {"timestamp": "2024-06-01T10:00:00", "level": "INFO",  "message": "started"},
    {"timestamp": "2024-06-01T10:00:01", "level": "ERROR", "message": "boom"},
    {"timestamp": "2024-06-01T10:00:02", "level": "INFO",  "message": "recovered"},
]


@pytest.fixture()
def log_path():
    path = _write_log(LOG_ENTRIES)
    yield path
    os.unlink(path)


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------

class TestConstruction:
    def test_pipeline_attribute_is_log_pipeline(self, log_path):
        rp = ReplayPipeline(log_path, speed=0)
        assert isinstance(rp.pipeline, LogPipeline)

    def test_replayer_attribute_is_log_replayer(self, log_path):
        rp = ReplayPipeline(log_path, speed=0)
        assert isinstance(rp.replayer, LogReplayer)

    def test_speed_forwarded_to_replayer(self, log_path):
        rp = ReplayPipeline(log_path, speed=5.0)
        assert rp.replayer.speed == 5.0


# ---------------------------------------------------------------------------
# Fluent API
# ---------------------------------------------------------------------------

class TestFluentAPI:
    def test_add_filter_returns_self(self, log_path):
        rp = ReplayPipeline(log_path, speed=0)
        result = rp.add_filter(RegexFilter("error"))
        assert result is rp

    def test_enrich_returns_self(self, log_path):
        rp = ReplayPipeline(log_path, speed=0)
        assert rp.enrich("env", "test") is rp


# ---------------------------------------------------------------------------
# Collect
# ---------------------------------------------------------------------------

class TestCollect:
    def test_no_filters_returns_all(self, log_path):
        rp = ReplayPipeline(log_path, speed=0)
        result = rp.collect()
        assert len(result) == 3

    def test_filter_reduces_results(self, log_path):
        rp = ReplayPipeline(log_path, speed=0)
        rp.add_filter(RegexFilter("error", field="level"))
        result = rp.collect()
        assert len(result) == 1
        assert result[0]["level"] == "ERROR"

    def test_enrich_adds_field(self, log_path):
        rp = ReplayPipeline(log_path, speed=0)
        rp.enrich("env", "staging")
        result = rp.collect()
        assert all(e["env"] == "staging" for e in result)

    def test_stream_yields_same_as_collect(self, log_path):
        rp = ReplayPipeline(log_path, speed=0)
        assert list(rp.stream()) == rp.collect()

    def test_callback_fires_during_replay(self, log_path):
        seen = []
        rp = ReplayPipeline(log_path, speed=0, on_entry=lambda e: seen.append(e["level"]))
        rp.collect()
        assert seen == ["INFO", "ERROR", "INFO"]
