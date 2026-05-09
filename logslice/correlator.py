"""LogCorrelator – group log entries by a shared correlation ID field."""

from __future__ import annotations

from collections import defaultdict
from typing import Callable, Dict, Iterable, Iterator, List, Optional


class LogCorrelator:
    """Collect log entries and group them by a correlation key.

    Parameters
    ----------
    field:
        The entry field used as the correlation key (default ``"correlation_id"``).
    missing:
        Value used when the field is absent in an entry (default ``"unknown"``).
    transform:
        Optional callable applied to the raw field value before grouping.
    """

    def __init__(
        self,
        field: str = "correlation_id",
        missing: str = "unknown",
        transform: Optional[Callable[[str], str]] = None,
    ) -> None:
        if not field:
            raise ValueError("field must be a non-empty string")
        self._field = field
        self._missing = missing
        self._transform = transform
        self._groups: Dict[str, List[dict]] = defaultdict(list)

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def field(self) -> str:
        return self._field

    @property
    def missing(self) -> str:
        return self._missing

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def feed(self, entry: dict) -> str:
        """Add *entry* to the appropriate group and return the resolved key."""
        raw = entry.get(self._field, self._missing)
        key = str(raw) if raw is not None else self._missing
        if self._transform is not None:
            key = self._transform(key)
        self._groups[key].append(entry)
        return key

    def feed_many(self, entries: Iterable[dict]) -> "LogCorrelator":
        """Feed multiple entries; returns *self* for chaining."""
        for entry in entries:
            self.feed(entry)
        return self

    def groups(self) -> Dict[str, List[dict]]:
        """Return a plain dict mapping correlation key → list of entries."""
        return dict(self._groups)

    def get(self, key: str) -> List[dict]:
        """Return all entries for *key*, or an empty list if unknown."""
        return list(self._groups.get(key, []))

    def keys(self) -> List[str]:
        """Return sorted list of known correlation keys."""
        return sorted(self._groups.keys())

    def stream(self, key: str) -> Iterator[dict]:
        """Yield entries for *key* one at a time."""
        yield from self._groups.get(key, [])

    def reset(self) -> "LogCorrelator":
        """Clear all accumulated groups; returns *self*."""
        self._groups.clear()
        return self
