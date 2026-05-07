"""Tests for logslice.router.LogRouter."""

import pytest
from logslice.router import LogRouter
from logslice.filters import RegexFilter, TimeRangeFilter


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _entry(level="info", message="hello", timestamp="2024-01-01T10:00:00"):
    return {"level": level, "message": message, "timestamp": timestamp}


# ---------------------------------------------------------------------------
# routing logic
# ---------------------------------------------------------------------------

def test_matching_rule_returns_correct_bucket():
    router = LogRouter()
    router.add_rule("errors", RegexFilter("error", field="level"))
    bucket = router.route(_entry(level="error"))
    assert bucket == "errors"


def test_non_matching_entry_goes_to_fallback():
    router = LogRouter(fallback="misc")
    router.add_rule("errors", RegexFilter("error", field="level"))
    bucket = router.route(_entry(level="info"))
    assert bucket == "misc"


def test_first_matching_rule_wins():
    router = LogRouter()
    router.add_rule("first", RegexFilter("err", field="level"))
    router.add_rule("second", RegexFilter("error", field="level"))
    router.route(_entry(level="error"))
    assert len(router.bucket("first")) == 1
    assert len(router.bucket("second")) == 0


def test_route_many_populates_buckets():
    router = LogRouter()
    router.add_rule("errors", RegexFilter("error", field="level"))
    entries = [
        _entry(level="error"),
        _entry(level="info"),
        _entry(level="error"),
    ]
    router.route_many(entries)
    assert len(router.bucket("errors")) == 2
    assert len(router.bucket("default")) == 1


def test_buckets_property_returns_snapshot():
    router = LogRouter()
    router.add_rule("errors", RegexFilter("error", field="level"))
    router.route(_entry(level="error"))
    snap = router.buckets
    assert "errors" in snap
    assert isinstance(snap["errors"], list)


def test_callback_invoked_on_match():
    collected = []
    router = LogRouter()
    router.add_rule("errors", RegexFilter("error", field="level"))
    router.on("errors", collected.append)
    router.route(_entry(level="error"))
    assert len(collected) == 1
    assert collected[0]["level"] == "error"


def test_callback_not_invoked_for_other_bucket():
    collected = []
    router = LogRouter()
    router.add_rule("errors", RegexFilter("error", field="level"))
    router.on("errors", collected.append)
    router.route(_entry(level="info"))  # goes to default
    assert collected == []


def test_clear_removes_entries_but_keeps_rules():
    router = LogRouter()
    router.add_rule("errors", RegexFilter("error", field="level"))
    router.route(_entry(level="error"))
    router.clear()
    assert router.bucket("errors") == []
    # rules still work after clear
    router.route(_entry(level="error"))
    assert len(router.bucket("errors")) == 1


def test_empty_bucket_returns_empty_list():
    router = LogRouter()
    assert router.bucket("nonexistent") == []


def test_chaining_add_rule_returns_self():
    router = LogRouter()
    result = router.add_rule("x", RegexFilter("x", field="level"))
    assert result is router


def test_chaining_on_returns_self():
    router = LogRouter()
    router.add_rule("x", RegexFilter("x", field="level"))
    result = router.on("x", lambda e: None)
    assert result is router
