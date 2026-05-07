"""Tests for logslice.dispatch.LogDispatcher."""

import json
import os
import tempfile
import pytest

from logslice.dispatch import LogDispatcher
from logslice.router import LogRouter
from logslice.filters import RegexFilter


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _write_log(lines):
    """Write JSON-lines to a temp file and return its path."""
    fd, path = tempfile.mkstemp(suffix=".log")
    with os.fdopen(fd, "w") as fh:
        for line in lines:
            fh.write(json.dumps(line) + "\n")
    return path


@pytest.fixture()
def log_path():
    entries = [
        {"level": "error", "message": "boom"},
        {"level": "info", "message": "all good"},
        {"level": "error", "message": "another failure"},
        {"level": "warning", "message": "watch out"},
    ]
    path = _write_log(entries)
    yield path
    os.unlink(path)


# ---------------------------------------------------------------------------
# tests
# ---------------------------------------------------------------------------

def test_run_returns_router(log_path):
    dispatcher = LogDispatcher(log_path)
    result = dispatcher.run()
    assert result is dispatcher.router


def test_errors_routed_correctly(log_path):
    dispatcher = LogDispatcher(log_path)
    dispatcher.router.add_rule("errors", RegexFilter("error", field="level"))
    dispatcher.run()
    assert len(dispatcher.router.bucket("errors")) == 2


def test_default_bucket_captures_unmatched(log_path):
    dispatcher = LogDispatcher(log_path)
    dispatcher.router.add_rule("errors", RegexFilter("error", field="level"))
    dispatcher.run()
    # info + warning go to default
    assert len(dispatcher.router.bucket("default")) == 2


def test_bucket_counts_reflects_distribution(log_path):
    dispatcher = LogDispatcher(log_path)
    dispatcher.router.add_rule("errors", RegexFilter("error", field="level"))
    dispatcher.run()
    counts = dispatcher.bucket_counts()
    assert counts["errors"] == 2
    assert counts["default"] == 2


def test_custom_router_accepted(log_path):
    custom_router = LogRouter(fallback="other")
    custom_router.add_rule("warnings", RegexFilter("warning", field="level"))
    dispatcher = LogDispatcher(log_path, router=custom_router)
    dispatcher.run()
    assert len(dispatcher.router.bucket("warnings")) == 1
    assert dispatcher.router is custom_router


def test_empty_log_produces_empty_buckets():
    path = _write_log([])
    try:
        dispatcher = LogDispatcher(path)
        dispatcher.run()
        assert dispatcher.router.buckets == {}
    finally:
        os.unlink(path)
