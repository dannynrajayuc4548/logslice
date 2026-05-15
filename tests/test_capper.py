"""Tests for logslice.capper.LogCapper."""
import pytest

from logslice.capper import LogCapper


def _entries(n: int) -> list[dict]:
    return [{"index": i, "message": f"msg-{i}"} for i in range(n)]


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------

def test_limit_stored():
    c = LogCapper(5)
    assert c.limit == 5


def test_default_skip_is_zero():
    c = LogCapper(3)
    assert c.skip == 0


def test_custom_skip_stored():
    c = LogCapper(3, skip=2)
    assert c.skip == 2


def test_zero_limit_raises():
    with pytest.raises(ValueError, match="limit"):
        LogCapper(0)


def test_negative_limit_raises():
    with pytest.raises(ValueError, match="limit"):
        LogCapper(-1)


def test_non_int_limit_raises():
    with pytest.raises(ValueError, match="limit"):
        LogCapper(2.5)  # type: ignore[arg-type]


def test_negative_skip_raises():
    with pytest.raises(ValueError, match="skip"):
        LogCapper(5, skip=-1)


# ---------------------------------------------------------------------------
# stream / collect
# ---------------------------------------------------------------------------

def test_collect_returns_list():
    result = LogCapper(3).collect(_entries(10))
    assert isinstance(result, list)


def test_limit_caps_output():
    result = LogCapper(4).collect(_entries(10))
    assert len(result) == 4


def test_limit_larger_than_source_returns_all():
    result = LogCapper(100).collect(_entries(5))
    assert len(result) == 5


def test_first_entries_returned():
    result = LogCapper(3).collect(_entries(10))
    assert [e["index"] for e in result] == [0, 1, 2]


def test_skip_discards_leading_entries():
    result = LogCapper(3, skip=2).collect(_entries(10))
    assert [e["index"] for e in result] == [2, 3, 4]


def test_skip_plus_limit_exceeds_source():
    result = LogCapper(10, skip=8).collect(_entries(10))
    assert [e["index"] for e in result] == [8, 9]


def test_stream_is_lazy():
    """stream() should return an iterator, not a list."""
    import types
    c = LogCapper(3)
    result = c.stream(_entries(10))
    assert isinstance(result, types.GeneratorType)


def test_empty_source_returns_empty():
    assert LogCapper(5).collect([]) == []


def test_entries_not_mutated():
    entries = _entries(5)
    result = LogCapper(5).collect(entries)
    assert result == entries
