"""Tests for logslice.windower."""

import pytest

from logslice.windower import LogWindower


def _entries(n: int, level: str = "INFO"):
    return [{"id": i, "level": level, "timestamp": f"2024-01-{i+1:02d}"} for i in range(n)]


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------

def test_default_step_equals_size():
    w = LogWindower(size=4)
    assert w.step == 4


def test_custom_step_stored():
    w = LogWindower(size=5, step=2)
    assert w.step == 2


def test_ts_field_stored():
    w = LogWindower(size=3, ts_field="timestamp")
    assert w.ts_field == "timestamp"


def test_default_ts_field_is_none():
    w = LogWindower(size=3)
    assert w.ts_field is None


def test_size_less_than_one_raises():
    with pytest.raises(ValueError, match="size"):
        LogWindower(size=0)


def test_step_less_than_one_raises():
    with pytest.raises(ValueError, match="step"):
        LogWindower(size=3, step=0)


def test_step_greater_than_size_raises():
    with pytest.raises(ValueError, match="step"):
        LogWindower(size=3, step=4)


# ---------------------------------------------------------------------------
# Tumbling windows (step == size)
# ---------------------------------------------------------------------------

def test_tumbling_window_count():
    w = LogWindower(size=3)
    result = w.collect(_entries(9))
    assert len(result) == 3


def test_tumbling_window_each_has_correct_count():
    w = LogWindower(size=3)
    for win in w.collect(_entries(9)):
        assert win["count"] == 3


def test_tumbling_window_no_overlap():
    w = LogWindower(size=3)
    windows = w.collect(_entries(6))
    ids_0 = {e["id"] for e in windows[0]["entries"]}
    ids_1 = {e["id"] for e in windows[1]["entries"]}
    assert ids_0.isdisjoint(ids_1)


def test_partial_window_not_emitted():
    # 7 entries with size=3 → 2 full windows (6 entries), last entry dropped
    w = LogWindower(size=3)
    assert len(w.collect(_entries(7))) == 2


# ---------------------------------------------------------------------------
# Sliding windows (step < size)
# ---------------------------------------------------------------------------

def test_sliding_window_count():
    # size=3, step=1 over 5 entries → 3 windows
    w = LogWindower(size=3, step=1)
    assert len(w.collect(_entries(5))) == 3


def test_sliding_window_overlap():
    w = LogWindower(size=3, step=1)
    windows = w.collect(_entries(5))
    ids_0 = {e["id"] for e in windows[0]["entries"]}
    ids_1 = {e["id"] for e in windows[1]["entries"]}
    assert not ids_0.isdisjoint(ids_1)


# ---------------------------------------------------------------------------
# ts_field
# ---------------------------------------------------------------------------

def test_ts_field_populated():
    w = LogWindower(size=2, ts_field="timestamp")
    windows = w.collect(_entries(4))
    for win in windows:
        assert "ts" in win
        assert win["ts"] is not None


def test_ts_field_first_entry_value():
    w = LogWindower(size=2, ts_field="timestamp")
    windows = w.collect(_entries(4))
    assert windows[0]["ts"] == "2024-01-01"
    assert windows[1]["ts"] == "2024-01-03"


def test_no_ts_key_when_ts_field_none():
    w = LogWindower(size=2)
    for win in w.collect(_entries(4)):
        assert "ts" not in win


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

def test_empty_input_yields_nothing():
    w = LogWindower(size=3)
    assert w.collect([]) == []


def test_fewer_entries_than_size_yields_nothing():
    w = LogWindower(size=5)
    assert w.collect(_entries(3)) == []


def test_windows_generator_is_lazy():
    w = LogWindower(size=2)
    gen = w.windows(_entries(4))
    import types
    assert isinstance(gen, types.GeneratorType)
