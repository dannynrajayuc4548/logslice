"""Tests for logslice.resume.stream_from_checkpoint."""

import json
import time
import threading
import pytest

from logslice.checkpoint import LogCheckpoint
from logslice.resume import stream_from_checkpoint


def _write_jsonl(path, entries):
    with open(path, "w", encoding="utf-8") as fh:
        for e in entries:
            fh.write(json.dumps(e) + "\n")


@pytest.fixture()
def log_file(tmp_path):
    p = tmp_path / "app.log"
    _write_jsonl(
        str(p),
        [
            {"ts": "2024-01-01T00:00:00", "level": "INFO", "msg": "boot"},
            {"ts": "2024-01-01T00:00:01", "level": "WARN", "msg": "slow"},
            {"ts": "2024-01-01T00:00:02", "level": "ERROR", "msg": "crash"},
        ],
    )
    return str(p)


@pytest.fixture()
def cp(tmp_path):
    return LogCheckpoint(str(tmp_path / "ckpt.json"))


# ---------------------------------------------------------------------------
# Basic streaming
# ---------------------------------------------------------------------------

def test_yields_all_lines_from_start(log_file, cp):
    entries = list(stream_from_checkpoint(log_file, cp, follow=False))
    assert len(entries) == 3


def test_entries_contain_raw_key(log_file, cp):
    entries = list(stream_from_checkpoint(log_file, cp, follow=False))
    for e in entries:
        assert "_raw" in e


def test_checkpoint_updated_after_stream(log_file, cp):
    list(stream_from_checkpoint(log_file, cp, follow=False))
    assert cp.load(log_file) is not None
    assert cp.load(log_file) > 0


def test_max_lines_limits_output(log_file, cp):
    entries = list(stream_from_checkpoint(log_file, cp, follow=False, max_lines=2))
    assert len(entries) == 2


def test_checkpoint_after_max_lines_is_partial(log_file, cp):
    list(stream_from_checkpoint(log_file, cp, follow=False, max_lines=1))
    offset_after_one = cp.load(log_file)
    list(stream_from_checkpoint(log_file, cp, follow=False, max_lines=1))
    offset_after_two = cp.load(log_file)
    assert offset_after_two > offset_after_one


def test_resume_skips_already_processed_lines(log_file, cp):
    # Consume first two lines.
    list(stream_from_checkpoint(log_file, cp, follow=False, max_lines=2))
    saved = cp.load(log_file)
    # Now resume — should only get the third line.
    remaining = list(stream_from_checkpoint(log_file, cp, follow=False))
    assert len(remaining) == 1
    assert remaining[0].get("msg") == "crash" or "crash" in remaining[0].get("_raw", "")


def test_no_checkpoint_starts_from_zero(log_file, cp):
    # Ensure no prior checkpoint exists.
    assert cp.load(log_file) is None
    entries = list(stream_from_checkpoint(log_file, cp, follow=False))
    assert len(entries) == 3
