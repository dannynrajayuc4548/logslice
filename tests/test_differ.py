"""Tests for logslice.differ."""
from __future__ import annotations

import pytest

from logslice.differ import LogDiffer, _default_key


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _e(id_: str, level: str = "INFO", msg: str = "hello") -> dict:
    return {"id": id_, "level": level, "message": msg}


# ---------------------------------------------------------------------------
# _default_key
# ---------------------------------------------------------------------------

def test_default_key_uses_id():
    assert _default_key({"id": "abc", "raw": "ignored"}) == "abc"


def test_default_key_falls_back_to_raw():
    assert _default_key({"raw": "line1"}) == "line1"


def test_default_key_empty_entry_gives_empty_string():
    assert _default_key({}) == ""


# ---------------------------------------------------------------------------
# construction
# ---------------------------------------------------------------------------

def test_default_key_stored():
    d = LogDiffer()
    assert callable(d.key)


def test_custom_key_stored():
    fn = lambda e: e["id"]
    d = LogDiffer(key=fn)
    assert d.key is fn


def test_compare_fields_none_by_default():
    assert LogDiffer().compare_fields is None


def test_compare_fields_stored():
    d = LogDiffer(compare_fields=["level", "message"])
    assert d.compare_fields == ["level", "message"]


# ---------------------------------------------------------------------------
# diff – status classification
# ---------------------------------------------------------------------------

def test_added_entry_detected():
    d = LogDiffer()
    results = dict(d.diff([], [_e("1")]))
    assert results["1"]["id"] == "1"
    statuses = [s for s, _ in d.diff([], [_e("1")])]
    assert statuses == ["added"]


def test_removed_entry_detected():
    d = LogDiffer()
    statuses = [s for s, _ in d.diff([_e("1")], [])]
    assert statuses == ["removed"]


def test_unchanged_entry_detected():
    entry = _e("1")
    d = LogDiffer()
    statuses = [s for s, _ in d.diff([entry], [entry.copy()])]
    assert statuses == ["unchanged"]


def test_changed_entry_detected():
    d = LogDiffer()
    left = [_e("1", level="INFO")]
    right = [_e("1", level="ERROR")]
    statuses = [s for s, _ in d.diff(left, right)]
    assert statuses == ["changed"]


def test_changed_entry_yields_right_version():
    d = LogDiffer()
    left = [_e("1", level="INFO")]
    right = [_e("1", level="ERROR")]
    _, entry = next(d.diff(left, right))
    assert entry["level"] == "ERROR"


def test_mixed_statuses():
    d = LogDiffer()
    left = [_e("1"), _e("2")]
    right = [_e("2"), _e("3")]
    result = {k: s for s, e in d.diff(left, right) for k in [e["id"]]}
    assert result["1"] == "removed"
    assert result["2"] == "unchanged"
    assert result["3"] == "added"


# ---------------------------------------------------------------------------
# compare_fields restriction
# ---------------------------------------------------------------------------

def test_compare_fields_ignores_other_fields():
    d = LogDiffer(compare_fields=["level"])
    left = [_e("1", level="INFO", msg="old message")]
    right = [_e("1", level="INFO", msg="new message")]
    statuses = [s for s, _ in d.diff(left, right)]
    # message differs but we only compare level → unchanged
    assert statuses == ["unchanged"]


def test_compare_fields_detects_change_in_watched_field():
    d = LogDiffer(compare_fields=["level"])
    left = [_e("1", level="INFO")]
    right = [_e("1", level="WARN")]
    statuses = [s for s, _ in d.diff(left, right)]
    assert statuses == ["changed"]


# ---------------------------------------------------------------------------
# only_changes
# ---------------------------------------------------------------------------

def test_only_changes_excludes_unchanged():
    d = LogDiffer()
    left = [_e("1"), _e("2")]
    right = [_e("1"), _e("2", level="ERROR")]
    statuses = [s for s, _ in d.only_changes(left, right)]
    assert "unchanged" not in statuses
    assert "changed" in statuses


def test_only_changes_empty_when_identical():
    entries = [_e("1"), _e("2")]
    d = LogDiffer()
    result = list(d.only_changes(entries, [e.copy() for e in entries]))
    assert result == []
