"""Tests for logslice.ratelimiter.LogRateLimiter."""

import pytest
from unittest.mock import patch
from logslice.ratelimiter import LogRateLimiter


def _entries(n: int):
    return [{"level": "INFO", "msg": f"entry {i}"} for i in range(n)]


# ---------------------------------------------------------------------------
# Construction validation
# ---------------------------------------------------------------------------

def test_raises_on_non_positive_rate():
    with pytest.raises(ValueError, match="rate must be positive"):
        LogRateLimiter(rate=0)


def test_raises_on_negative_rate():
    with pytest.raises(ValueError, match="rate must be positive"):
        LogRateLimiter(rate=-5)


def test_raises_on_zero_burst():
    with pytest.raises(ValueError, match="burst must be >= 1"):
        LogRateLimiter(rate=10, burst=0)


def test_properties_stored():
    rl = LogRateLimiter(rate=5.0, burst=3)
    assert rl.rate == 5.0
    assert rl.burst == 3


# ---------------------------------------------------------------------------
# Streaming / passthrough
# ---------------------------------------------------------------------------

def test_stream_yields_all_entries():
    rl = LogRateLimiter(rate=1000.0, burst=1000)
    data = _entries(10)
    result = list(rl.stream(data))
    assert result == data


def test_stream_preserves_entry_content():
    rl = LogRateLimiter(rate=100.0)
    data = [{"level": "ERROR", "msg": "boom"}]
    result = list(rl.stream(data))
    assert result[0]["msg"] == "boom"


def test_empty_stream_returns_empty():
    rl = LogRateLimiter(rate=10.0)
    assert list(rl.stream([])) == []


# ---------------------------------------------------------------------------
# Rate-limiting behaviour (injectable clock + sleep)
# ---------------------------------------------------------------------------

def test_no_sleep_when_burst_not_exceeded():
    """With burst=5 and only 3 entries, sleep should never be called."""
    rl = LogRateLimiter(rate=5.0, burst=5)
    sleep_calls = []
    clock = [0.0]

    def fake_now():
        return clock[0]

    def fake_sleep(t):
        sleep_calls.append(t)
        clock[0] += t

    result = list(rl.stream(_entries(3), _sleep=fake_sleep, _now=fake_now))
    assert len(result) == 3
    assert sleep_calls == []


def test_sleep_called_when_burst_exceeded():
    """With burst=1 and rate=1, the second entry must trigger a sleep."""
    rl = LogRateLimiter(rate=1.0, burst=1)
    sleep_calls = []
    clock = [0.0]

    def fake_now():
        return clock[0]

    def fake_sleep(t):
        sleep_calls.append(t)
        clock[0] += t

    result = list(rl.stream(_entries(3), _sleep=fake_sleep, _now=fake_now))
    assert len(result) == 3
    assert len(sleep_calls) >= 2


def test_sleep_duration_is_positive():
    rl = LogRateLimiter(rate=2.0, burst=1)
    sleep_calls = []
    clock = [0.0]

    def fake_now():
        return clock[0]

    def fake_sleep(t):
        assert t > 0, "sleep must be called with a positive duration"
        sleep_calls.append(t)
        clock[0] += t

    list(rl.stream(_entries(4), _sleep=fake_sleep, _now=fake_now))
