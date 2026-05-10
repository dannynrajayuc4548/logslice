"""Tests for logslice.archiver.LogArchiver."""

import json
import os
import gzip
import pytest

from logslice.archiver import LogArchiver


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _entries(n: int = 5):
    return [
        {"timestamp": f"2024-01-01T00:00:0{i}", "level": "INFO", "msg": f"line {i}"}
        for i in range(n)
    ]


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------

def test_path_stored(tmp_path):
    arc = LogArchiver(str(tmp_path / "out.jsonl.gz"))
    assert arc.path == str(tmp_path / "out.jsonl.gz")


def test_default_mode_is_write(tmp_path):
    arc = LogArchiver(str(tmp_path / "out.jsonl.gz"))
    assert arc.mode == "write"


def test_append_mode_stored(tmp_path):
    arc = LogArchiver(str(tmp_path / "out.jsonl.gz"), mode="append")
    assert arc.mode == "append"


def test_invalid_mode_raises(tmp_path):
    with pytest.raises(ValueError, match="mode"):
        LogArchiver(str(tmp_path / "out.jsonl.gz"), mode="read")


# ---------------------------------------------------------------------------
# archive()
# ---------------------------------------------------------------------------

def test_archive_returns_count(tmp_path):
    arc = LogArchiver(str(tmp_path / "out.jsonl.gz"))
    assert arc.archive(_entries(4)) == 4


def test_archive_creates_file(tmp_path):
    p = str(tmp_path / "out.jsonl.gz")
    LogArchiver(p).archive(_entries(2))
    assert os.path.isfile(p)


def test_archive_file_is_gzip(tmp_path):
    p = str(tmp_path / "out.jsonl.gz")
    LogArchiver(p).archive(_entries(2))
    with gzip.open(p, "rb") as fh:
        data = fh.read()
    assert len(data) > 0


def test_write_mode_overwrites(tmp_path):
    p = str(tmp_path / "out.jsonl.gz")
    LogArchiver(p).archive(_entries(5))
    LogArchiver(p, mode="write").archive(_entries(2))
    entries = list(LogArchiver(p).read())
    assert len(entries) == 2


def test_append_mode_accumulates(tmp_path):
    p = str(tmp_path / "out.jsonl.gz")
    LogArchiver(p, mode="write").archive(_entries(3))
    LogArchiver(p, mode="append").archive(_entries(2))
    entries = list(LogArchiver(p).read())
    assert len(entries) == 5


# ---------------------------------------------------------------------------
# read()
# ---------------------------------------------------------------------------

def test_read_round_trips_entries(tmp_path):
    p = str(tmp_path / "out.jsonl.gz")
    original = _entries(3)
    LogArchiver(p).archive(original)
    recovered = list(LogArchiver(p).read())
    assert recovered == original


def test_read_empty_archive(tmp_path):
    p = str(tmp_path / "empty.jsonl.gz")
    LogArchiver(p).archive([])
    assert list(LogArchiver(p).read()) == []


# ---------------------------------------------------------------------------
# exists() / size()
# ---------------------------------------------------------------------------

def test_exists_false_before_write(tmp_path):
    arc = LogArchiver(str(tmp_path / "missing.jsonl.gz"))
    assert arc.exists() is False


def test_exists_true_after_write(tmp_path):
    p = str(tmp_path / "out.jsonl.gz")
    arc = LogArchiver(p)
    arc.archive(_entries(1))
    assert arc.exists() is True


def test_size_zero_when_missing(tmp_path):
    arc = LogArchiver(str(tmp_path / "missing.jsonl.gz"))
    assert arc.size() == 0


def test_size_positive_after_write(tmp_path):
    p = str(tmp_path / "out.jsonl.gz")
    arc = LogArchiver(p)
    arc.archive(_entries(10))
    assert arc.size() > 0
