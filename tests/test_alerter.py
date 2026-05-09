"""Tests for LogAlerter."""

import pytest

from logslice.alerter import LogAlerter


def _entries():
    return [
        {"level": "INFO", "message": "started"},
        {"level": "ERROR", "message": "boom"},
        {"level": "ERROR", "message": "crash"},
        {"level": "DEBUG", "message": "verbose"},
    ]


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------

def test_starts_with_no_rules():
    a = LogAlerter()
    assert a.rule_names == []


def test_add_rule_returns_self():
    a = LogAlerter()
    result = a.add_rule("r", lambda e: True, lambda n, e: None)
    assert result is a


def test_empty_name_raises():
    a = LogAlerter()
    with pytest.raises(ValueError, match="non-empty"):
        a.add_rule("", lambda e: True, lambda n, e: None)


def test_rule_names_in_insertion_order():
    a = LogAlerter()
    a.add_rule("alpha", lambda e: True, lambda n, e: None)
    a.add_rule("beta", lambda e: True, lambda n, e: None)
    assert a.rule_names == ["alpha", "beta"]


# ---------------------------------------------------------------------------
# feed()
# ---------------------------------------------------------------------------

def test_no_rules_yields_no_triggered():
    a = LogAlerter()
    result = a.feed(_entries())
    assert result == []


def test_matching_entries_are_triggered():
    fired = []
    a = LogAlerter()
    a.add_rule(
        "errors",
        condition=lambda e: e.get("level") == "ERROR",
        callback=lambda name, entry: fired.append((name, entry)),
    )
    triggered = a.feed(_entries())
    assert len(triggered) == 2
    assert all(t["rule"] == "errors" for t in triggered)


def test_callback_receives_name_and_entry():
    received = []
    a = LogAlerter()
    a.add_rule(
        "catch-all",
        condition=lambda e: True,
        callback=lambda name, entry: received.append((name, entry)),
    )
    a.feed([{"level": "INFO"}])
    assert received[0][0] == "catch-all"
    assert received[0][1] == {"level": "INFO"}


def test_triggered_property_reflects_last_feed():
    a = LogAlerter()
    a.add_rule("e", lambda e: e.get("level") == "ERROR", lambda n, e: None)
    a.feed(_entries())
    assert len(a.triggered) == 2
    # second feed clears previous results
    a.feed([{"level": "INFO"}])
    assert len(a.triggered) == 0


def test_multiple_rules_can_match_same_entry():
    a = LogAlerter()
    a.add_rule("r1", lambda e: True, lambda n, e: None)
    a.add_rule("r2", lambda e: True, lambda n, e: None)
    triggered = a.feed([{"level": "INFO"}])
    assert len(triggered) == 2


def test_faulty_condition_does_not_crash_feed():
    """A condition that raises should be silently skipped."""
    a = LogAlerter()
    a.add_rule("bad", lambda e: 1 / 0, lambda n, e: None)
    result = a.feed([{"level": "INFO"}])
    assert result == []


def test_triggered_entry_contains_entry_key():
    a = LogAlerter()
    a.add_rule("x", lambda e: True, lambda n, e: None)
    triggered = a.feed([{"msg": "hello"}])
    assert triggered[0]["entry"] == {"msg": "hello"}
