"""Tests for LogNormalizer and NormalizePipeline."""
from __future__ import annotations

import json
import os
import tempfile

import pytest

from logslice.normalizer import LogNormalizer
from logslice.normalize_pipeline import NormalizePipeline


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _e(**kwargs):
    return dict(kwargs)


def _write_log(path: str, entries):
    with open(path, "w") as fh:
        for e in entries:
            fh.write(json.dumps(e) + "\n")


# ---------------------------------------------------------------------------
# LogNormalizer — alias
# ---------------------------------------------------------------------------

class TestAlias:
    def test_renames_key(self):
        norm = LogNormalizer().alias("lvl", "level")
        out = norm.apply(_e(lvl="info", message="hi"))
        assert "level" in out
        assert "lvl" not in out

    def test_unknown_key_left_unchanged(self):
        norm = LogNormalizer().alias("lvl", "level")
        out = norm.apply(_e(severity="warn"))
        assert out == {"severity": "warn"}

    def test_returns_self_for_chaining(self):
        norm = LogNormalizer()
        assert norm.alias("a", "b") is norm

    def test_empty_old_key_raises(self):
        with pytest.raises(ValueError):
            LogNormalizer().alias("", "level")

    def test_empty_new_key_raises(self):
        with pytest.raises(ValueError):
            LogNormalizer().alias("lvl", "")


# ---------------------------------------------------------------------------
# LogNormalizer — coerce
# ---------------------------------------------------------------------------

class TestCoerce:
    def test_transforms_value(self):
        norm = LogNormalizer().coerce("level", str.upper)
        out = norm.apply(_e(level="info"))
        assert out["level"] == "INFO"

    def test_missing_key_is_noop(self):
        norm = LogNormalizer().coerce("level", str.upper)
        out = norm.apply(_e(message="hi"))
        assert out == {"message": "hi"}

    def test_coerce_applied_after_alias(self):
        norm = LogNormalizer().alias("lvl", "level").coerce("level", str.upper)
        out = norm.apply(_e(lvl="debug"))
        assert out["level"] == "DEBUG"

    def test_non_callable_raises(self):
        with pytest.raises(TypeError):
            LogNormalizer().coerce("level", "upper")  # type: ignore

    def test_returns_self_for_chaining(self):
        norm = LogNormalizer()
        assert norm.coerce("level", str.upper) is norm


# ---------------------------------------------------------------------------
# LogNormalizer — stream / collect
# ---------------------------------------------------------------------------

class TestStream:
    def test_stream_yields_all_entries(self):
        norm = LogNormalizer().alias("lvl", "level")
        entries = [_e(lvl="info"), _e(lvl="error")]
        out = list(norm.stream(entries))
        assert len(out) == 2
        assert all("level" in e for e in out)

    def test_collect_returns_list(self):
        norm = LogNormalizer()
        result = norm.collect([_e(a=1), _e(a=2)])
        assert isinstance(result, list)
        assert len(result) == 2

    def test_original_entry_not_mutated(self):
        norm = LogNormalizer().alias("lvl", "level")
        original = _e(lvl="warn")
        norm.apply(original)
        assert "lvl" in original
        assert "level" not in original


# ---------------------------------------------------------------------------
# NormalizePipeline
# ---------------------------------------------------------------------------

class TestNormalizePipeline:
    def test_pipeline_attribute(self):
        from logslice.pipeline import LogPipeline
        with tempfile.NamedTemporaryFile(delete=False, suffix=".log") as f:
            path = f.name
        try:
            p = NormalizePipeline(path)
            assert isinstance(p.pipeline, LogPipeline)
        finally:
            os.unlink(path)

    def test_normalizer_attribute(self):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".log") as f:
            path = f.name
        try:
            p = NormalizePipeline(path)
            assert isinstance(p.normalizer, LogNormalizer)
        finally:
            os.unlink(path)

    def test_collect_applies_alias(self):
        entries = [{"lvl": "info", "message": "ok"}]
        with tempfile.NamedTemporaryFile(
            mode="w", delete=False, suffix=".log"
        ) as f:
            _write_log(f.name, entries)
            path = f.name
        try:
            result = NormalizePipeline(path).alias("lvl", "level").collect()
            assert all("level" in e for e in result)
            assert all("lvl" not in e for e in result)
        finally:
            os.unlink(path)

    def test_chaining_returns_self(self):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".log") as f:
            path = f.name
        try:
            p = NormalizePipeline(path)
            assert p.alias("a", "b") is p
            assert p.coerce("b", str.upper) is p
        finally:
            os.unlink(path)
