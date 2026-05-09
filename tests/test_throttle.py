"""Tests for logslice.throttle.LogThrottle."""

import pytest

from logslice.throttle import LogThrottle, _default_key


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _e(level="ERROR", message="boom") -> dict:
    return {"level": level, "message": message}


class _FakeClock:
    """Monotonically advancing fake clock."""

    def __init__(self, start: float = 0.0):
        self.t = start

    def __call__(self) -> float:
        return self.t

    def advance(self, seconds: float) -> None:
        self.t += seconds


# ---------------------------------------------------------------------------
# _default_key
# ---------------------------------------------------------------------------

def test_default_key_uses_level_and_message():
    assert _default_key({"level": "INFO", "message": "hi"}) == "INFO::hi"


def test_default_key_falls_back_to_msg():
    assert _default_key({"level": "WARN", "msg": "x"}) == "WARN::x"


def test_default_key_falls_back_to_raw():
    assert _default_key({"raw": "plain line"}) == "::plain line"


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------

def test_negative_window_raises():
    with pytest.raises(ValueError, match="window"):
        LogThrottle(window=-1)


def test_zero_window_allowed():
    t = LogThrottle(window=0)
    assert t.window == 0


def test_initial_counters_are_zero():
    t = LogThrottle(window=5)
    assert t.suppressed == 0
    assert t.passed == 0


# ---------------------------------------------------------------------------
# allow()
# ---------------------------------------------------------------------------

def test_first_occurrence_always_passes():
    clock = _FakeClock()
    t = LogThrottle(window=10, clock=clock)
    assert t.allow(_e()) is True
    assert t.passed == 1
    assert t.suppressed == 0


def test_duplicate_within_window_suppressed():
    clock = _FakeClock()
    t = LogThrottle(window=10, clock=clock)
    t.allow(_e())
    clock.advance(5)  # still inside window
    assert t.allow(_e()) is False
    assert t.suppressed == 1


def test_duplicate_after_window_passes():
    clock = _FakeClock()
    t = LogThrottle(window=10, clock=clock)
    t.allow(_e())
    clock.advance(10)  # exactly at boundary → allowed
    assert t.allow(_e()) is True
    assert t.passed == 2


def test_different_messages_are_independent():
    clock = _FakeClock()
    t = LogThrottle(window=60, clock=clock)
    assert t.allow(_e(message="alpha")) is True
    assert t.allow(_e(message="beta")) is True
    assert t.passed == 2
    assert t.suppressed == 0


# ---------------------------------------------------------------------------
# stream()
# ---------------------------------------------------------------------------

def test_stream_filters_duplicates():
    clock = _FakeClock()
    t = LogThrottle(window=30, clock=clock)
    entries = [_e(), _e(), _e(message="other"), _e()]
    result = list(t.stream(entries))
    assert len(result) == 2
    assert result[0]["message"] == "boom"
    assert result[1]["message"] == "other"


def test_stream_empty_input():
    t = LogThrottle(window=5)
    assert list(t.stream([])) == []


# ---------------------------------------------------------------------------
# reset()
# ---------------------------------------------------------------------------

def test_reset_clears_seen_keys():
    clock = _FakeClock()
    t = LogThrottle(window=60, clock=clock)
    t.allow(_e())
    t.reset()
    # After reset the same entry should pass again
    assert t.allow(_e()) is True


def test_reset_does_not_clear_counters():
    clock = _FakeClock()
    t = LogThrottle(window=60, clock=clock)
    t.allow(_e())
    t.allow(_e())  # suppressed
    t.reset()
    assert t.passed == 1
    assert t.suppressed == 1


# ---------------------------------------------------------------------------
# Custom key function
# ---------------------------------------------------------------------------

def test_custom_key_fn_respected():
    clock = _FakeClock()
    # Group everything by level only
    t = LogThrottle(window=60, key_fn=lambda e: e.get("level", ""), clock=clock)
    assert t.allow(_e(message="first")) is True
    assert t.allow(_e(message="second")) is False  # same level → suppressed
