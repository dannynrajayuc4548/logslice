"""Tests for LogMasker and MaskPipeline."""
from __future__ import annotations

import json
import os
import tempfile
from typing import Dict, Any

import pytest

from logslice.masker import LogMasker
from logslice.mask_pipeline import MaskPipeline


def _e(**kwargs: Any) -> Dict[str, Any]:
    base = {"timestamp": "2024-01-01T00:00:00", "level": "INFO", "message": "ok"}
    base.update(kwargs)
    return base


def _write_log(entries):
    tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False)
    for e in entries:
        tmp.write(json.dumps(e) + "\n")
    tmp.close()
    return tmp.name


# ---------------------------------------------------------------------------
# LogMasker construction
# ---------------------------------------------------------------------------

def test_default_placeholder():
    m = LogMasker()
    assert m.placeholder == "***"


def test_custom_placeholder_stored():
    m = LogMasker(placeholder="[REDACTED]")
    assert m.placeholder == "[REDACTED]"


def test_empty_placeholder_raises():
    with pytest.raises(ValueError):
        LogMasker(placeholder="")


# ---------------------------------------------------------------------------
# mask_full
# ---------------------------------------------------------------------------

def test_mask_full_replaces_entire_value():
    m = LogMasker()
    m.mask_full("password")
    result = m.apply(_e(password="s3cr3t"))
    assert result["password"] == "***"


def test_mask_full_missing_field_is_noop():
    m = LogMasker()
    m.mask_full("token")
    entry = _e()
    result = m.apply(entry)
    assert "token" not in result


def test_mask_full_non_string_field_is_noop():
    m = LogMasker()
    m.mask_full("count")
    entry = _e(count=42)
    result = m.apply(entry)
    assert result["count"] == 42


def test_mask_full_empty_field_raises():
    m = LogMasker()
    with pytest.raises(ValueError):
        m.mask_full("")


# ---------------------------------------------------------------------------
# mask_pattern
# ---------------------------------------------------------------------------

def test_mask_pattern_replaces_match():
    m = LogMasker()
    m.mask_pattern("message", r"\d+")
    result = m.apply(_e(message="user 42 logged in"))
    assert result["message"] == "user *** logged in"


def test_mask_pattern_no_match_leaves_value():
    m = LogMasker()
    m.mask_pattern("message", r"\d+")
    result = m.apply(_e(message="no numbers here"))
    assert result["message"] == "no numbers here"


def test_mask_pattern_empty_field_raises():
    m = LogMasker()
    with pytest.raises(ValueError):
        m.mask_pattern("", r"\d+")


def test_mask_pattern_case_insensitive_flag():
    import re
    m = LogMasker(placeholder="<X>")
    m.mask_pattern("message", r"error", flags=re.IGNORECASE)
    result = m.apply(_e(message="ERROR occurred"))
    assert result["message"] == "<X> occurred"


# ---------------------------------------------------------------------------
# apply does not mutate original
# ---------------------------------------------------------------------------

def test_apply_does_not_mutate_original():
    m = LogMasker()
    m.mask_full("secret")
    original = _e(secret="abc")
    m.apply(original)
    assert original["secret"] == "abc"


# ---------------------------------------------------------------------------
# stream
# ---------------------------------------------------------------------------

def test_stream_yields_masked_entries():
    m = LogMasker()
    m.mask_full("token")
    entries = [_e(token="t1"), _e(token="t2")]
    results = list(m.stream(entries))
    assert all(r["token"] == "***" for r in results)


# ---------------------------------------------------------------------------
# MaskPipeline
# ---------------------------------------------------------------------------

def test_pipeline_and_masker_attributes():
    from logslice.pipeline import LogPipeline
    mp = MaskPipeline.__new__(MaskPipeline)
    mp.__init__("dummy.log")
    assert isinstance(mp.masker, LogMasker)


def test_mask_pipeline_collect(tmp_path):
    path = _write_log([_e(token="abc"), _e(token="xyz")])
    try:
        mp = MaskPipeline(path)
        mp.mask_full("token")
        results = mp.collect()
        assert len(results) == 2
        assert all(r["token"] == "***" for r in results)
    finally:
        os.unlink(path)


def test_mask_pipeline_chaining_returns_self():
    mp = MaskPipeline("dummy.log")
    result = mp.mask_full("x").mask_pattern("y", r"a")
    assert result is mp
