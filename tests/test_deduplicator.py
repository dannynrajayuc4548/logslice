"""Tests for logslice.deduplicator."""

import pytest

from logslice.deduplicator import LogDeduplicator, _default_key


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _e(msg: str, level: str = "INFO") -> dict:
    return {"message": msg, "level": level}


# ---------------------------------------------------------------------------
# _default_key
# ---------------------------------------------------------------------------

def test_default_key_same_content_same_hash():
    a = {"message": "hello", "level": "INFO"}
    b = {"message": "hello", "level": "INFO"}
    assert _default_key(a) == _default_key(b)


def test_default_key_different_content_different_hash():
    assert _default_key(_e("a")) != _default_key(_e("b"))


# ---------------------------------------------------------------------------
# feed / stream
# ---------------------------------------------------------------------------

def test_feed_removes_exact_duplicates():
    entries = [_e("x"), _e("x"), _e("y")]
    result = LogDeduplicator().feed(entries)
    assert result == [_e("x"), _e("y")]


def test_first_occurrence_kept():
    a = {"message": "dup", "level": "INFO"}
    b = {"message": "dup", "level": "ERROR"}  # different — not a dup
    result = LogDeduplicator().feed([a, b, a])
    assert result == [a, b]


def test_stream_is_lazy_iterator():
    entries = [_e("a"), _e("a"), _e("b")]
    gen = LogDeduplicator().stream(entries)
    assert next(gen) == _e("a")
    assert next(gen) == _e("b")
    with pytest.raises(StopIteration):
        next(gen)


def test_empty_input_returns_empty():
    assert LogDeduplicator().feed([]) == []


# ---------------------------------------------------------------------------
# custom key_fn
# ---------------------------------------------------------------------------

def test_custom_key_fn_deduplicates_by_message_only():
    dedup = LogDeduplicator(key_fn=lambda e: e["message"])
    entries = [
        {"message": "same", "level": "INFO"},
        {"message": "same", "level": "ERROR"},  # same message → duplicate
        {"message": "other", "level": "DEBUG"},
    ]
    result = dedup.feed(entries)
    assert len(result) == 2
    assert result[0]["level"] == "INFO"
    assert result[1]["message"] == "other"


# ---------------------------------------------------------------------------
# max_seen eviction
# ---------------------------------------------------------------------------

def test_max_seen_evicts_oldest_key():
    dedup = LogDeduplicator(max_seen=2)
    e1, e2, e3 = _e("a"), _e("b"), _e("c")
    dedup.feed([e1, e2, e3])  # e1 evicted after e3 inserted
    # e1 should no longer be in seen → feeding it again should pass through
    result = dedup.feed([e1])
    assert result == [e1]


def test_seen_count_tracks_unique_entries():
    dedup = LogDeduplicator()
    dedup.feed([_e("a"), _e("b"), _e("a")])
    assert dedup.seen_count == 2


# ---------------------------------------------------------------------------
# reset
# ---------------------------------------------------------------------------

def test_reset_clears_seen_cache():
    dedup = LogDeduplicator()
    dedup.feed([_e("x")])
    assert dedup.seen_count == 1
    dedup.reset()
    assert dedup.seen_count == 0
    # after reset same entry is no longer a duplicate
    assert dedup.feed([_e("x")]) == [_e("x")]
