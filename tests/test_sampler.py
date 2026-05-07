"""Tests for logslice.sampler."""

import pytest

from logslice.sampler import LogSampler


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _entries(n: int, level: str = "INFO") -> list:
    return [{"level": level, "msg": f"msg-{i}"} for i in range(n)]


# ---------------------------------------------------------------------------
# Construction validation
# ---------------------------------------------------------------------------

def test_raises_when_neither_option_given():
    with pytest.raises(ValueError, match="Provide either"):
        LogSampler()


def test_raises_when_both_options_given():
    with pytest.raises(ValueError):
        LogSampler(rate=0.5, reservoir_size=10)


def test_raises_on_invalid_rate():
    with pytest.raises(ValueError, match="rate must be"):
        LogSampler(rate=1.5)


def test_raises_on_zero_reservoir():
    with pytest.raises(ValueError, match="reservoir_size"):
        LogSampler(reservoir_size=0)


# ---------------------------------------------------------------------------
# Rate sampling
# ---------------------------------------------------------------------------

def test_rate_zero_returns_empty():
    sampler = LogSampler(rate=0.0, seed=42)
    assert sampler.sample(_entries(100)) == []


def test_rate_one_returns_all():
    sampler = LogSampler(rate=1.0, seed=42)
    assert len(sampler.sample(_entries(50))) == 50


def test_rate_half_returns_roughly_half(benchmark=None):
    sampler = LogSampler(rate=0.5, seed=0)
    result = sampler.sample(_entries(1000))
    assert 400 <= len(result) <= 600


def test_stream_yields_same_as_sample():
    sampler_a = LogSampler(rate=0.4, seed=7)
    sampler_b = LogSampler(rate=0.4, seed=7)
    entries = _entries(200)
    assert list(sampler_a.stream(entries)) == sampler_b.sample(entries)


def test_stream_raises_in_reservoir_mode():
    sampler = LogSampler(reservoir_size=5, seed=1)
    with pytest.raises(RuntimeError, match="stream\(\)"):
        list(sampler.stream(_entries(10)))


# ---------------------------------------------------------------------------
# Reservoir sampling
# ---------------------------------------------------------------------------

def test_reservoir_exact_size():
    sampler = LogSampler(reservoir_size=10, seed=99)
    result = sampler.sample(_entries(200))
    assert len(result) == 10


def test_reservoir_smaller_input_than_size():
    sampler = LogSampler(reservoir_size=50, seed=1)
    result = sampler.sample(_entries(20))
    assert len(result) == 20


def test_reservoir_entries_are_original_dicts():
    sampler = LogSampler(reservoir_size=5, seed=3)
    entries = _entries(20)
    result = sampler.sample(entries)
    for item in result:
        assert item in entries


# ---------------------------------------------------------------------------
# Transform
# ---------------------------------------------------------------------------

def test_transform_applied_in_rate_mode():
    def upper(e):
        return {k: v.upper() if isinstance(v, str) else v for k, v in e.items()}

    sampler = LogSampler(rate=1.0, seed=0, transform=upper)
    result = sampler.sample([{"level": "info", "msg": "hello"}])
    assert result[0]["level"] == "INFO"
    assert result[0]["msg"] == "HELLO"


def test_transform_applied_in_reservoir_mode():
    def tag(e):
        return {**e, "sampled": True}

    sampler = LogSampler(reservoir_size=3, seed=5, transform=tag)
    result = sampler.sample(_entries(10))
    assert all(r.get("sampled") is True for r in result)
