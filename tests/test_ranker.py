"""Tests for LogRanker and RankPipeline."""
from __future__ import annotations

import json
import tempfile
import os

import pytest

from logslice.ranker import LogRanker
from logslice.rank_pipeline import RankPipeline


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _e(score=None, **kw) -> dict:
    entry = {"message": "log line"}
    if score is not None:
        entry["score"] = score
    entry.update(kw)
    return entry


def _write_log(entries) -> str:
    fd, path = tempfile.mkstemp(suffix=".jsonl")
    with os.fdopen(fd, "w") as fh:
        for e in entries:
            fh.write(json.dumps(e) + "\n")
    return path


# ---------------------------------------------------------------------------
# LogRanker construction
# ---------------------------------------------------------------------------

def test_default_field_is_score():
    r = LogRanker()
    assert r.field == "score"


def test_default_rank_field_is_rank():
    r = LogRanker()
    assert r.rank_field == "rank"


def test_custom_field_stored():
    r = LogRanker(field="priority")
    assert r.field == "priority"


def test_empty_field_raises():
    with pytest.raises(ValueError):
        LogRanker(field="")


def test_empty_rank_field_raises():
    with pytest.raises(ValueError):
        LogRanker(rank_field="   ")


def test_default_default_is_zero():
    r = LogRanker()
    assert r.default == 0.0


def test_default_reverse_is_false():
    r = LogRanker()
    assert r.reverse is False


# ---------------------------------------------------------------------------
# LogRanker.rank behaviour
# ---------------------------------------------------------------------------

def test_highest_score_gets_rank_one():
    entries = [_e(score=10), _e(score=30), _e(score=20)]
    ranked = LogRanker().rank(entries)
    rank_map = {e["score"]: e["rank"] for e in ranked}
    assert rank_map[30] == 1
    assert rank_map[20] == 2
    assert rank_map[10] == 3


def test_reverse_true_lowest_gets_rank_one():
    entries = [_e(score=10), _e(score=30), _e(score=20)]
    ranked = LogRanker(reverse=True).rank(entries)
    rank_map = {e["score"]: e["rank"] for e in ranked}
    assert rank_map[10] == 1
    assert rank_map[20] == 2
    assert rank_map[30] == 3


def test_missing_field_uses_default():
    entries = [_e(), _e(score=5)]
    ranked = LogRanker(default=0.0).rank(entries)
    # score=5 should be rank 1, missing (treated as 0) should be rank 2
    score5 = next(e for e in ranked if e.get("score") == 5)
    assert score5["rank"] == 1


def test_rank_field_written_to_output():
    entries = [_e(score=1)]
    ranked = LogRanker(rank_field="position").rank(entries)
    assert "position" in ranked[0]


def test_original_entry_not_mutated():
    original = _e(score=42)
    LogRanker().rank([original])
    assert "rank" not in original


def test_empty_input_returns_empty_list():
    assert LogRanker().rank([]) == []


def test_stream_yields_same_as_rank():
    entries = [_e(score=i) for i in range(5)]
    r = LogRanker()
    assert list(r.stream(entries)) == r.rank(entries)


# ---------------------------------------------------------------------------
# RankPipeline
# ---------------------------------------------------------------------------

def test_pipeline_attribute_is_log_pipeline():
    from logslice.pipeline import LogPipeline
    path = _write_log([])
    try:
        rp = RankPipeline(path)
        assert isinstance(rp.pipeline, LogPipeline)
    finally:
        os.unlink(path)


def test_ranker_attribute_is_log_ranker():
    path = _write_log([])
    try:
        rp = RankPipeline(path)
        assert isinstance(rp.ranker, LogRanker)
    finally:
        os.unlink(path)


def test_run_returns_ranked_list():
    entries = [
        {"level": "INFO", "score": 5, "message": "a"},
        {"level": "INFO", "score": 15, "message": "b"},
        {"level": "INFO", "score": 10, "message": "c"},
    ]
    path = _write_log(entries)
    try:
        result = RankPipeline(path).run()
        assert result[0]["score"] == 15
        assert result[0]["rank"] == 1
    finally:
        os.unlink(path)


def test_stream_yields_all_entries():
    entries = [{"score": i, "message": "x"} for i in range(4)]
    path = _write_log(entries)
    try:
        result = list(RankPipeline(path).stream())
        assert len(result) == 4
    finally:
        os.unlink(path)


def test_add_filter_returns_self():
    from logslice.filters import RegexFilter
    path = _write_log([])
    try:
        rp = RankPipeline(path)
        assert rp.add_filter(RegexFilter(".")) is rp
    finally:
        os.unlink(path)


def test_custom_field_forwarded_to_ranker():
    path = _write_log([])
    try:
        rp = RankPipeline(path, field="priority")
        assert rp.ranker.field == "priority"
    finally:
        os.unlink(path)
