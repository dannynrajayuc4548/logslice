"""Exporter module for writing filtered log output to files or streams."""

import io
import json
from typing import Iterable, IO, Optional


class LogExporter:
    """Exports processed log entries to various output targets."""

    def __init__(self, formatter=None):
        """
        Args:
            formatter: Optional formatter instance. If None, entries are
                       written as plain strings using str().
        """
        self._formatter = formatter

    def _render(self, entry: dict) -> str:
        if self._formatter is not None:
            return self._formatter.format(entry)
        return str(entry)

    def to_file(self, entries: Iterable[dict], path: str, mode: str = "w") -> int:
        """Write entries to a file path.

        Args:
            entries: Iterable of log entry dicts.
            path: Destination file path.
            mode: File open mode (default 'w').

        Returns:
            Number of entries written.
        """
        count = 0
        with open(path, mode, encoding="utf-8") as fh:
            for entry in entries:
                fh.write(self._render(entry) + "\n")
                count += 1
        return count

    def to_stream(self, entries: Iterable[dict], stream: IO[str]) -> int:
        """Write entries to an open stream.

        Args:
            entries: Iterable of log entry dicts.
            stream: A writable text stream.

        Returns:
            Number of entries written.
        """
        count = 0
        for entry in entries:
            stream.write(self._render(entry) + "\n")
            count += 1
        return count

    def to_jsonl(self, entries: Iterable[dict], path: str, mode: str = "w") -> int:
        """Write entries as JSON Lines format.

        Args:
            entries: Iterable of log entry dicts.
            path: Destination file path.
            mode: File open mode (default 'w').

        Returns:
            Number of entries written.
        """
        count = 0
        with open(path, mode, encoding="utf-8") as fh:
            for entry in entries:
                fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
                count += 1
        return count
