"""LogGrouper – bucket log entries by a field value and apply per-group callbacks."""
from __future__ import annotations

from collections import defaultdict
from typing import Callable, Dict, Iterable, Iterator, List, Optional


class LogGrouper:
    """Group log entries by the value of a chosen field.

    Parameters
    ----------
    field:
        The entry key whose value determines the bucket.  Defaults to ``"level"``.
    default:
        Label used when the field is absent or ``None``.  Defaults to ``"unknown"``.
    """

    def __init__(self, field: str = "level", default: str = "unknown") -> None:
        if not field or not field.strip():
            raise ValueError("field must be a non-empty string")
        if not default or not default.strip():
            raise ValueError("default must be a non-empty string")
        self._field = field
        self._default = default
        self._buckets: Dict[str, List[dict]] = defaultdict(list)
        self._hooks: Dict[str, List[Callable[[dict], None]]] = defaultdict(list)

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
    def buckets(self) -> Dict[str, List[dict]]:
        """Snapshot of all accumulated buckets."""
        return dict(self._buckets)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def on_group(self, key: str, callback: Callable[[dict], None]) -> "LogGrouper":
        """Register *callback* to be invoked for every entry routed to *key*."""
        if not callable(callback):
            raise TypeError("callback must be callable")
        self._hooks[key].append(callback)
        return self

    def feed(self, entry: dict) -> str:
        """Add *entry* to the appropriate bucket and fire any registered hooks.

        Returns the bucket key the entry was placed in.
        """
        key = str(entry.get(self._field) or self._default)
        self._buckets[key].append(entry)
        for cb in self._hooks.get(key, []):
            cb(entry)
        return key

    def feed_many(self, entries: Iterable[dict]) -> Dict[str, int]:
        """Feed multiple entries; return a dict of bucket -> count added."""
        counts: Dict[str, int] = defaultdict(int)
        for entry in entries:
            counts[self.feed(entry)] += 1
        return dict(counts)

    def stream(self, key: str) -> Iterator[dict]:
        """Yield all entries stored under *key*."""
        yield from self._buckets.get(key, [])

    def keys(self) -> List[str]:
        """Return sorted list of bucket keys seen so far."""
        return sorted(self._buckets.keys())

    def clear(self) -> None:
        """Remove all accumulated entries from every bucket."""
        self._buckets.clear()
