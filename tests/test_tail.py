"""Integration-style tests for the tail() and stream_live() helpers."""

import threading
import time

from logslice.tail import tail, stream_live


def _write_lines(path: str, lines, delay: float = 0.0) -> None:
    """Append *lines* to *path*, optionally waiting *delay* seconds first."""
    if delay:
        time.sleep(delay)
    with open(path, "a", encoding="utf-8") as fh:
        for line in lines:
            fh.write(line + "\n")


class TestTailHelper:
    def test_returns_list(self, tmp_path):
        log = tmp_path / "t.log"
        log.write_text("x\ny\n", encoding="utf-8")
        result = tail(str(log), n=5, from_start=True)
        assert isinstance(result, list)

    def test_from_start_true_returns_all_lines(self, tmp_path):
        """When from_start=True all existing lines should be returned."""
        log = tmp_path / "all.log"
        log.write_text("a\nb\nc\n", encoding="utf-8")
        result = tail(str(log), n=10, from_start=True)
        assert result == ["a", "b", "c"]

    def test_from_start_false_catches_new_lines(self, tmp_path):
        log = tmp_path / "t.log"
        log.write_text("old\n", encoding="utf-8")

        # Schedule a write after tail() has set up the watcher
        threading.Thread(
            target=_write_lines,
            args=(str(log), ["new1", "new2"]),
            kwargs={"delay": 0.15},
        ).start()

        result = tail(str(log), n=2, from_start=False)
        assert "old" not in result
        assert "new1" in result
        assert "new2" in result

    def test_empty_file_returns_empty_list(self, tmp_path):
        log = tmp_path / "empty.log"
        log.write_text("", encoding="utf-8")
        result = tail(str(log), n=5, from_start=True)
        assert result == []


class TestStreamLive:
    def test_stream_live_yields_new_entries(self, tmp_path):
        log = tmp_path / "live.log"
        log.write_text("", encoding="utf-8")

        collected = []

        def _consume():
            for entry in stream_live(str(log)):
                collected.append(entry)
                if len(collected) >= 3:
                    break

        t = threading.Thread(target=_consume, daemon=True)
        t.start()

        time.sleep(0.1)
        _write_lines(str(log), ["alpha", "beta", "gamma"])
        t.join(timeout=3.0)

        assert collected == ["alpha", "beta", "gamma"]

    def test_stream_live_skips_historical(self, tmp_path):
        log = tmp_path / "hist.log"
        log.write_text("historic\n", encoding="utf-8")

        collected = []

        def _consume():
            for entry in stream_live(str(log)):
                collected.append(entry)
                if len(collected) >= 1:
                    break

        t = threading.Thread(target=_consume, daemon=True)
        t.start()

        time.sleep(0.1)
        _write_lines(str(log), ["fresh"])
        t.join(timeout=3.0)

        assert "historic" not in collected
        assert "fresh" in collected
