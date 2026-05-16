"""Tests for logslice.clamper.LogClamper."""
import pytest
from logslice.clamper import LogClamper


def _e(**kwargs):
    return dict(kwargs)


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------

def test_default_lo_is_none():
    c = LogClamper("score", hi=100)
    assert c.lo is None


def test_default_hi_is_none():
    c = LogClamper("score", lo=0)
    assert c.hi is None


def test_custom_lo_and_hi_stored():
    c = LogClamper("score", lo=1, hi=10)
    assert c.lo == 1
    assert c.hi == 10


def test_field_stored():
    c = LogClamper("latency", lo=0, hi=500)
    assert c.field == "latency"


def test_empty_field_raises():
    with pytest.raises(ValueError, match="non-empty"):
        LogClamper("", lo=0, hi=10)


def test_whitespace_field_raises():
    with pytest.raises(ValueError, match="non-empty"):
        LogClamper("   ", lo=0, hi=10)


def test_lo_greater_than_hi_raises():
    with pytest.raises(ValueError, match="lo"):
        LogClamper("score", lo=10, hi=5)


def test_lo_equal_to_hi_allowed():
    c = LogClamper("score", lo=5, hi=5)
    assert c.lo == c.hi == 5


def test_coerce_default_is_false():
    c = LogClamper("score")
    assert c.coerce is False


def test_coerce_true_stored():
    c = LogClamper("score", coerce=True)
    assert c.coerce is True


# ---------------------------------------------------------------------------
# apply — basic clamping
# ---------------------------------------------------------------------------

def test_value_below_lo_raised_to_lo():
    c = LogClamper("score", lo=0, hi=100)
    result = c.apply(_e(score=-5))
    assert result["score"] == 0


def test_value_above_hi_lowered_to_hi():
    c = LogClamper("score", lo=0, hi=100)
    result = c.apply(_e(score=200))
    assert result["score"] == 100


def test_value_within_range_unchanged():
    c = LogClamper("score", lo=0, hi=100)
    result = c.apply(_e(score=50))
    assert result["score"] == 50


def test_no_lower_bound_allows_very_small_values():
    c = LogClamper("score", hi=100)
    result = c.apply(_e(score=-9999))
    assert result["score"] == -9999


def test_no_upper_bound_allows_very_large_values():
    c = LogClamper("score", lo=0)
    result = c.apply(_e(score=9999))
    assert result["score"] == 9999


def test_missing_field_entry_returned_unchanged():
    c = LogClamper("score", lo=0, hi=100)
    entry = _e(level="info")
    assert c.apply(entry) == entry


def test_apply_does_not_mutate_original():
    c = LogClamper("score", lo=0, hi=10)
    original = _e(score=50)
    c.apply(original)
    assert original["score"] == 50


# ---------------------------------------------------------------------------
# coerce
# ---------------------------------------------------------------------------

def test_string_numeric_clamped_when_coerce_true():
    c = LogClamper("score", lo=0, hi=10, coerce=True)
    result = c.apply(_e(score="15"))
    assert result["score"] == 10.0


def test_non_numeric_string_left_unchanged_when_coerce_true():
    c = LogClamper("score", lo=0, hi=10, coerce=True)
    result = c.apply(_e(score="abc"))
    assert result["score"] == "abc"


def test_non_numeric_left_unchanged_when_coerce_false():
    c = LogClamper("score", lo=0, hi=10)
    result = c.apply(_e(score="high"))
    assert result["score"] == "high"


# ---------------------------------------------------------------------------
# stream / collect
# ---------------------------------------------------------------------------

def test_stream_yields_all_entries():
    c = LogClamper("v", lo=0, hi=5)
    entries = [_e(v=i) for i in range(10)]
    results = list(c.stream(entries))
    assert len(results) == 10


def test_collect_returns_list():
    c = LogClamper("v", lo=0, hi=5)
    assert isinstance(c.collect([_e(v=3)]), list)


def test_stream_clamps_multiple_entries():
    c = LogClamper("v", lo=1, hi=3)
    entries = [_e(v=0), _e(v=2), _e(v=5)]
    results = c.collect(entries)
    assert [r["v"] for r in results] == [1, 2, 3]


def test_float_value_clamped_correctly():
    c = LogClamper("latency", lo=0.0, hi=1.0)
    result = c.apply(_e(latency=1.5))
    assert result["latency"] == 1.0
