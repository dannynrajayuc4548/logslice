"""Tests for logslice.compressor.LogCompressor."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from logslice.compressor import LogCompressor


def _entries(n: int = 5) -> list[dict]:
    return [
        {"timestamp": f"2024-01-01T00:00:0{i}", "level": "INFO", "message": f"msg {i}"}
        for i in range(n)
    ]


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------

def test_default_mode_is_gz():
    c = LogCompressor("/tmp/out.log")
    assert c.mode == "gz"


def test_bz2_mode_stored():
    c = LogCompressor("/tmp/out.log", mode="bz2")
    assert c.mode == "bz2"


def test_invalid_mode_raises():
    with pytest.raises(ValueError, match="mode must be one of"):
        LogCompressor("/tmp/out.log", mode="xz")  # type: ignore[arg-type]


def test_extension_appended_automatically(tmp_path):
    c = LogCompressor(tmp_path / "archive")
    assert c.path.suffix == ".gz"


def test_existing_correct_extension_not_doubled(tmp_path):
    c = LogCompressor(tmp_path / "archive.gz")
    assert c.path.name == "archive.gz"


def test_bz2_extension_appended(tmp_path):
    c = LogCompressor(tmp_path / "archive", mode="bz2")
    assert c.path.suffix == ".bz2"


# ---------------------------------------------------------------------------
# compress / decompress round-trip
# ---------------------------------------------------------------------------

def test_compress_returns_count(tmp_path):
    c = LogCompressor(tmp_path / "out")
    entries = _entries(7)
    assert c.compress(entries) == 7


def test_compress_creates_file(tmp_path):
    c = LogCompressor(tmp_path / "out")
    c.compress(_entries(3))
    assert c.path.exists()


def test_gz_round_trip(tmp_path):
    c = LogCompressor(tmp_path / "out", mode="gz")
    original = _entries(4)
    c.compress(original)
    recovered = c.decompress()
    assert recovered == original


def test_bz2_round_trip(tmp_path):
    c = LogCompressor(tmp_path / "out", mode="bz2")
    original = _entries(4)
    c.compress(original)
    recovered = c.decompress()
    assert recovered == original


def test_empty_entries_yields_empty_file(tmp_path):
    c = LogCompressor(tmp_path / "empty")
    count = c.compress([])
    assert count == 0
    assert c.decompress() == []


def test_parent_dirs_created(tmp_path):
    c = LogCompressor(tmp_path / "deep" / "nested" / "out")
    c.compress(_entries(2))
    assert c.path.exists()


def test_unicode_message_preserved(tmp_path):
    entry = {"message": "こんにちは", "level": "DEBUG"}
    c = LogCompressor(tmp_path / "unicode")
    c.compress([entry])
    assert c.decompress()[0]["message"] == "こんにちは"


def test_compress_overwrites_previous_file(tmp_path):
    c = LogCompressor(tmp_path / "out")
    c.compress(_entries(10))
    c.compress(_entries(2))
    assert len(c.decompress()) == 2
