"""Core log parser for reading and streaming structured log lines."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Generator, Iterable, Union

from .filters import BaseFilter


class LogParser:
    """Reads a log file line-by-line and applies a chain of filters."""

    def __init__(self, path: Union[str, Path], filters: list[BaseFilter] | None = None):
        self.path = Path(path)
        self.filters: list[BaseFilter] = filters or []

    def add_filter(self, f: BaseFilter) -> "LogParser":
        """Attach an additional filter and return self for chaining."""
        self.filters.append(f)
        return self

    def _parse_line(self, raw: str) -> dict | None:
        """Attempt to parse a raw log line as JSON; fall back to plain text."""
        raw = raw.rstrip("\n")
        if not raw:
            return None
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {"message": raw, "_raw": True}

    def stream(self) -> Generator[dict, None, None]:
        """Yield log records that pass all filters."""
        with self.path.open("r", encoding="utf-8", errors="replace") as fh:
            for raw_line in fh:
                record = self._parse_line(raw_line)
                if record is None:
                    continue
                if all(f.match(record) for f in self.filters):
                    yield record

    def to_list(self) -> list[dict]:
        """Collect all matching records into a list."""
        return list(self.stream())

    def count(self) -> int:
        """Return the number of matching records."""
        return sum(1 for _ in self.stream())
