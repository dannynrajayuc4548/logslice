"""Tests for LogProfiler and ProfilePipeline."""
from __future__ import annotations

import json
import os
import tempfile
import time
from typing import List

import pytest

from logslice.profiler import LogProfiler
from logslice.profile_pipeline import ProfilePipeline


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _entries(n: int = 5, base_ts: float = 1_000.0, step: float = 0.5) -> List[dict]:
    return [{"level": "INFO", "msg": f"msg {i}", "ts": base_ts + i * step} for i in range(n)]


class _FakeClock:
    def __init__(self, start: float = 0.0) -> None:
        self.t = start

    def __call__(self) -> float:
        return self.t

    def advance(self, delta: float) -> None:
        self.t += delta


def _write_log(entries: List[dict]) -> str:
    fd, path = tempfile.mkstemp(suffix=".jsonl")
    with os.fdopen(fd, "w") as fh:
        for e in entries:
            fh.write(json.dumps(e) + "\n")
    return path


# ---------------------------------------------------------------------------
# LogProfiler – construction
# ---------------------------------------------------------------------------

def test_default_count_is_zero():
    p = LogProfiler()
    assert p.count == 0


def test_blank_timestamp_field_raises():
    with pytest.raises(ValueError):
        LogProfiler(timestamp_field="   ")


def test_empty_timestamp_field_raises():
    with pytest.raises(ValueError):
        LogProfiler(timestamp_field="")


# ---------------------------------------------------------------------------
# LogProfiler – feed / stream
# ---------------------------------------------------------------------------

def test_feed_returns_entry_unchanged():
    p = LogProfiler()
    e = {"level": "ERROR", "msg": "boom"}
    result = p.feed(e)
    assert result is e


def test_count_increments():
    p = LogProfiler()
    for e in _entries(7):
        p.feed(e)
    assert p.count == 7


def test_stream_yields_all_entries():
    p = LogProfiler()
    entries = _entries(4)
    out = list(p.stream(entries))
    assert len(out) == 4
    assert out == entries


def test_elapsed_uses_clock():
    clock = _FakeClock(10.0)
    p = LogProfiler(clock=clock)
    p.feed({"msg": "a"})
    clock.advance(3.0)
    p.feed({"msg": "b"})
    assert abs(p.elapsed - 3.0) < 1e-9


def test_throughput_computed():
    clock = _FakeClock(0.0)
    p = LogProfiler(clock=clock)
    p.feed({"msg": "a"})
    clock.advance(2.0)
    p.feed({"msg": "b"})
    # 2 entries over 2 seconds → 1.0 eps
    assert abs(p.throughput - 1.0) < 1e-9


def test_throughput_zero_when_no_entries():
    p = LogProfiler()
    assert p.throughput == 0.0


# ---------------------------------------------------------------------------
# LogProfiler – latency tracking
# ---------------------------------------------------------------------------

def test_latencies_collected():
    p = LogProfiler(timestamp_field="ts")
    for e in _entries(5, base_ts=0.0, step=1.0):
        p.feed(e)
    lats = p.latencies
    assert len(lats) == 4
    assert all(abs(l - 1.0) < 1e-9 for l in lats)


def test_mean_latency_correct():
    p = LogProfiler(timestamp_field="ts")
    for e in _entries(3, base_ts=0.0, step=2.0):
        p.feed(e)
    assert abs(p.mean_latency - 2.0) < 1e-9


def test_mean_latency_none_when_no_samples():
    p = LogProfiler()
    p.feed({"msg": "x"})
    assert p.mean_latency is None


def test_non_numeric_ts_ignored():
    p = LogProfiler(timestamp_field="ts")
    p.feed({"ts": "not-a-number"})
    p.feed({"ts": "still-not"})
    assert p.latencies == []


# ---------------------------------------------------------------------------
# LogProfiler – reset / summary
# ---------------------------------------------------------------------------

def test_reset_clears_state():
    p = LogProfiler(timestamp_field="ts")
    for e in _entries(4):
        p.feed(e)
    p.reset()
    assert p.count == 0
    assert p.elapsed == 0.0
    assert p.latencies == []


def test_summary_keys():
    p = LogProfiler()
    p.feed({"msg": "hi"})
    s = p.summary()
    assert set(s.keys()) == {"count", "elapsed", "throughput", "mean_latency", "latency_samples"}


# ---------------------------------------------------------------------------
# ProfilePipeline
# ---------------------------------------------------------------------------

def test_pipeline_attribute_is_log_pipeline():
    from logslice.pipeline import LogPipeline
    path = _write_log(_entries(2))
    try:
        pp = ProfilePipeline(path)
        assert isinstance(pp.pipeline, LogPipeline)
    finally:
        os.unlink(path)


def test_profiler_attribute_is_log_profiler():
    path = _write_log(_entries(2))
    try:
        pp = ProfilePipeline(path)
        assert isinstance(pp.profiler, LogProfiler)
    finally:
        os.unlink(path)


def test_collect_returns_all_entries():
    entries = _entries(6)
    path = _write_log(entries)
    try:
        pp = ProfilePipeline(path)
        results = pp.collect()
        assert len(results) == 6
    finally:
        os.unlink(path)


def test_profiler_count_matches_collected():
    entries = _entries(5)
    path = _write_log(entries)
    try:
        pp = ProfilePipeline(path)
        results = pp.collect()
        assert pp.profiler.count == len(results)
    finally:
        os.unlink(path)


def test_add_filter_returns_self():
    from logslice.filters import RegexFilter
    path = _write_log(_entries(2))
    try:
        pp = ProfilePipeline(path)
        ret = pp.add_filter(RegexFilter("INFO"))
        assert ret is pp
    finally:
        os.unlink(path)


def test_timestamp_field_forwarded_to_profiler():
    entries = _entries(4, base_ts=100.0, step=1.0)
    path = _write_log(entries)
    try:
        pp = ProfilePipeline(path, timestamp_field="ts")
        pp.collect()
        assert pp.profiler.mean_latency is not None
    finally:
        os.unlink(path)
