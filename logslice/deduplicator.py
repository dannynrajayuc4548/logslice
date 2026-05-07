"""Deduplication support for structured log entries."""

import hashlib
import json
from typing import Callable, Iterable, Iterator, Optional


def _default_key(entry: dict) -> str:
    """Stable hash of the full entry contents."""
    serialised = json.dumps(entry, sort_keys=True, default=str)
    return hashlib.md5(serialised.encode()).hexdigest()


class LogDeduplicator:
    """Filter duplicate log entries from a stream.

    Parameters
    ----------
    key_fn:
        Callable that accepts a log entry dict and returns a hashable key.
        Defaults to a full-content MD5 hash.
    max_seen:
        Maximum number of keys to keep in memory.  Once the limit is reached
        the oldest key is evicted (FIFO).  ``None`` means unlimited.
    """

    def __init__(
        self,
        key_fn: Optional[Callable[[dict], str]] = None,
        max_seen: Optional[int] = None,
    ) -> None:
        self._key_fn: Callable[[dict], str] = key_fn or _default_key
        self._max_seen = max_seen
        self._seen: dict[str, None] = {}  # ordered insertion dict used as ordered set

    # ------------------------------------------------------------------
    def _is_duplicate(self, entry: dict) -> bool:
        key = self._key_fn(entry)
        if key in self._seen:
            return True
        # evict oldest entry when cap is reached
        if self._max_seen is not None and len(self._seen) >= self._max_seen:
            oldest = next(iter(self._seen))
            del self._seen[oldest]
        self._seen[key] = None
        return False

    def feed(self, entries: Iterable[dict]) -> list[dict]:
        """Return a list with duplicates removed (first occurrence kept)."""
        return list(self.stream(entries))

    def stream(self, entries: Iterable[dict]) -> Iterator[dict]:
        """Yield unique entries, skipping duplicates."""
        for entry in entries:
            if not self._is_duplicate(entry):
                yield entry

    def reset(self) -> None:
        """Clear the seen-key cache."""
        self._seen.clear()

    @property
    def seen_count(self) -> int:
        """Number of unique keys currently tracked."""
        return len(self._seen)
