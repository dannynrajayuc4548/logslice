"""Tests for LogWatcher and the tail() / stream_live() helpers."""

import os
import tempfile
import threading
import time

import pytest

from logslice.watcher import LogWatcher
from logslice.tail import tail
from logslice.parser import LogParser


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _append(path: str, lines, delay: float = 0.0) -> None:
    """Append *lines* to *path*, optionally with a small delay first."""
    if delay:
        time.sleep(delay)
    with open(path, "a", encoding="utf-8") as fh:
        for line in lines:
            fh.write(line + "\n")


# ---------------------------------------------------------------------------
# LogWatcher unit tests
# ---------------------------------------------------------------------------

class TestLogWatcher:
    def test_yields_existing_lines_from_offset_zero(self, tmp_path):
        log = tmp_path / "app.log"
        log.write_text("line1\nline2\nline3\n", encoding="utf-8")

        watcher = LogWatcher(str(log), poll_interval=0.05)
        results = list(watcher.follow(max_lines=3, timeout=1.0))
        assert results == ["line1", "line2", "line3"]

    def test_seek_end_skips_existing_content(self, tmp_path):
        log = tmp_path / "app.log"
        log.write_text("old_line\n", encoding="utf-8")

        watcher = LogWatcher(str(log), poll_interval=0.05)
        watcher.seek_end()

        # Append new content after seek_end
        threading.Thread(
            target=_append, args=([str(log)], ["new_line"]), kwargs={"delay": 0.1}
        ).start()

        results = list(watcher.follow(max_lines=1, timeout=2.0))
        assert results == ["new_line"]

    def test_custom_parser_applied(self, tmp_path):
        log = tmp_path / "app.log"
        log.write_text('{"level": "INFO", "msg": "ok"}\n', encoding="utf-8")

        import json
        watcher = LogWatcher(str(log), poll_interval=0.05, parser=json.loads)
        results = list(watcher.follow(max_lines=1, timeout=1.0))
        assert results == [{"level": "INFO", "msg": "ok"}]

    def test_empty_lines_are_skipped(self, tmp_path):
        log = tmp_path / "app.log"
        log.write_text("line1\n\nline2\n", encoding="utf-8")

        watcher = LogWatcher(str(log), poll_interval=0.05)
        results = list(watcher.follow(max_lines=2, timeout=1.0))
        assert results == ["line1", "line2"]

    def test_timeout_stops_iteration(self, tmp_path):
        log = tmp_path / "app.log"
        log.write_text("", encoding="utf-8")

        watcher = LogWatcher(str(log), poll_interval=0.05)
        results = list(watcher.follow(timeout=0.3))
        assert results == []

    def test_missing_file_waits_then_reads(self, tmp_path):
        log = tmp_path / "late.log"

        def _create():
            time.sleep(0.15)
            log.write_text("appeared\n", encoding="utf-8")

        threading.Thread(target=_create).start()
        watcher = LogWatcher(str(log), poll_interval=0.05)
        results = list(watcher.follow(max_lines=1, timeout=2.0))
        assert results == ["appeared"]


# ---------------------------------------------------------------------------
# tail() helper tests
# ---------------------------------------------------------------------------

class TestTail:
    def test_tail_from_start(self, tmp_path):
        log = tmp_path / "app.log"
        log.write_text("a\nb\nc\n", encoding="utf-8")
        result = tail(str(log), n=3, from_start=True)
        assert result == ["a", "b", "c"]

    def test_tail_respects_n(self, tmp_path):
        log = tmp_path / "app.log"
        log.write_text("a\nb\nc\nd\ne\n", encoding="utf-8")
        result = tail(str(log), n=2, from_start=True)
        assert len(result) == 2

    def test_tail_with_parser(self, tmp_path):
        log = tmp_path / "app.log"
        log.write_text(
            '{"level": "ERROR", "msg": "boom"}\n'
            '{"level": "INFO", "msg": "ok"}\n',
            encoding="utf-8",
        )
        parser = LogParser()
        result = tail(str(log), n=10, parser=parser, from_start=True)
        # _parse_line may return None for non-matching lines; filter them
        entries = [e for e in result if e is not None]
        assert any(isinstance(e, dict) for e in entries)
