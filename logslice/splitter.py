"""LogSplitter — split a stream of log entries into named buckets by field value."""

from __future__ import annotations

from collections import defaultdict
from typing import Callable, Dict, Iterable, Iterator, List, Optional


class LogSplitter:
    """Partition log entries into named buckets based on the value of a field.

    Parameters
    ----------
    field:
        The entry key whose value determines the bucket name.
    transform:
        Optional callable applied to the raw field value before it is used as
        a bucket name (e.g. ``str.lower``).
    default:
        Bucket name used when *field* is absent or the value is ``None``.
        Defaults to ``"unknown"``.
    """

    def __init__(
        self,
        field: str,
        transform: Optional[Callable[[str], str]] = None,
        default: str = "unknown",
    ) -> None:
        if not field:
            raise ValueError("field must be a non-empty string")
        self._field = field
        self._transform = transform
        self._default = default
        self._buckets: Dict[str, List[dict]] = defaultdict(list)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def field(self) -> str:
        return self._field

    @property
    def default(self) -> str:
        return self._default

    @property
    def buckets(self) -> Dict[str, List[dict]]:
        """Return the current bucket mapping (bucket name → list of entries)."""
        return dict(self._buckets)

    def feed(self, entries: Iterable[dict]) -> "LogSplitter":
        """Consume *entries* and place each one into the appropriate bucket.

        Returns *self* so calls can be chained.
        """
        for entry in entries:
            bucket = self._bucket_for(entry)
            self._buckets[bucket].append(entry)
        return self

    def stream(self, entries: Iterable[dict]) -> Iterator[tuple]:
        """Yield ``(bucket_name, entry)`` tuples without storing anything."""
        for entry in entries:
            yield self._bucket_for(entry), entry

    def bucket_names(self) -> List[str]:
        """Return a sorted list of bucket names seen so far."""
        return sorted(self._buckets.keys())

    def clear(self) -> "LogSplitter":
        """Reset all accumulated buckets."""
        self._buckets.clear()
        return self

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _bucket_for(self, entry: dict) -> str:
        raw = entry.get(self._field)
        if raw is None:
            return self._default
        value = str(raw)
        if self._transform is not None:
            value = self._transform(value)
        return value or self._default
