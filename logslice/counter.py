"""LogCounter — tracks rolling counts of log entries by a chosen field."""
from __future__ import annotations

from collections import defaultdict
from typing import Callable, Dict, Iterable, Iterator, List, Optional


class LogCounter:
    """Count log entries grouped by a field value over a sliding window.

    Parameters
    ----------
    field:
        The entry key whose value is used as the grouping key.
    default:
        Label used when the field is absent.  Defaults to ``"unknown"``.
    transform:
        Optional callable applied to the raw field value before counting.
    """

    def __init__(
        self,
        field: str = "level",
        default: str = "unknown",
        transform: Optional[Callable[[str], str]] = None,
    ) -> None:
        if not field:
            raise ValueError("field must be a non-empty string")
        self._field = field
        self._default = default
        self._transform = transform
        self._counts: Dict[str, int] = defaultdict(int)
        self._total: int = 0

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def field(self) -> str:
        return self._field

    @property
    def default(self) -> str:
        return self._default

    @property
    def total(self) -> int:
        return self._total

    # ------------------------------------------------------------------
    # Core API
    # ------------------------------------------------------------------

    def feed(self, entry: dict) -> "LogCounter":
        """Register a single log entry and increment the relevant counter."""
        raw = entry.get(self._field, self._default)
        if raw is None:
            raw = self._default
        key = str(raw)
        if self._transform is not None:
            key = self._transform(key)
        self._counts[key] += 1
        self._total += 1
        return self

    def feed_many(self, entries: Iterable[dict]) -> "LogCounter":
        """Feed an iterable of entries; returns *self* for chaining."""
        for entry in entries:
            self.feed(entry)
        return self

    def counts(self) -> Dict[str, int]:
        """Return a plain dict snapshot of current counts."""
        return dict(self._counts)

    def top(self, n: int = 5) -> List[tuple]:
        """Return the *n* most frequent (key, count) pairs, highest first."""
        return sorted(self._counts.items(), key=lambda kv: kv[1], reverse=True)[:n]

    def reset(self) -> "LogCounter":
        """Clear all counts and return *self*."""
        self._counts.clear()
        self._total = 0
        return self

    def stream(self, entries: Iterable[dict]) -> Iterator[dict]:
        """Pass-through iterator that counts entries as they flow through."""
        for entry in entries:
            self.feed(entry)
            yield entry
