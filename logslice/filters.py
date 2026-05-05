"""Built-in filter classes for logslice."""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Pattern


class BaseFilter(ABC):
    """Abstract base class for all log filters."""

    @abstractmethod
    def match(self, record: dict) -> bool:
        """Return True if *record* should be included in results."""


class RegexFilter(BaseFilter):
    """Include records whose *field* value matches *pattern*."""

    def __init__(self, pattern: str, field: str = "message", flags: int = 0):
        self.field = field
        self.pattern: Pattern = re.compile(pattern, flags)

    def match(self, record: dict) -> bool:
        value = record.get(self.field, "")
        return bool(self.pattern.search(str(value)))


class TimeRangeFilter(BaseFilter):
    """Include records whose timestamp falls within [start, end].

    The *field* value is parsed with *fmt* (strptime format string).
    Omit *start* or *end* to leave that boundary open.
    """

    def __init__(
        self,
        start: datetime | None = None,
        end: datetime | None = None,
        field: str = "timestamp",
        fmt: str = "%Y-%m-%dT%H:%M:%S",
    ):
        if start is None and end is None:
            raise ValueError("At least one of 'start' or 'end' must be provided.")
        self.start = start
        self.end = end
        self.field = field
        self.fmt = fmt

    def _parse_ts(self, value: str) -> datetime | None:
        try:
            return datetime.strptime(value[:19], self.fmt)
        except (ValueError, TypeError):
            return None

    def match(self, record: dict) -> bool:
        raw_ts = record.get(self.field)
        if raw_ts is None:
            return False
        ts = self._parse_ts(str(raw_ts))
        if ts is None:
            return False
        if self.start and ts < self.start:
            return False
        if self.end and ts > self.end:
            return False
        return True
