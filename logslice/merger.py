"""LogMerger – merge and chronologically sort entries from multiple log sources."""

from __future__ import annotations

import heapq
from typing import Callable, Iterable, Iterator, List, Optional, Tuple


_DEFAULT_TS_KEY = "timestamp"


class LogMerger:
    """Merge multiple iterables of log-entry dicts into a single sorted stream.

    Entries are sorted by a configurable timestamp key.  Sources that are
    missing the key are placed *after* all timestamped entries (stable order
    among themselves).

    Example::

        merger = LogMerger()
        merger.add_source(source_a)
        merger.add_source(source_b)
        for entry in merger.stream():
            print(entry)
    """

    def __init__(
        self,
        ts_key: str = _DEFAULT_TS_KEY,
        key_fn: Optional[Callable[[dict], any]] = None,
    ) -> None:
        """Initialise the merger.

        Args:
            ts_key:  Dict key used to extract the sort value when *key_fn* is
                     not provided.
            key_fn:  Optional callable that receives an entry dict and returns
                     a comparable sort key.  Overrides *ts_key* when given.
        """
        self._ts_key = ts_key
        self._key_fn: Callable[[dict], any] = key_fn or (lambda e: e.get(ts_key, ""))
        self._sources: List[Iterable[dict]] = []

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def add_source(self, source: Iterable[dict]) -> "LogMerger":
        """Register a log source (any iterable of dicts).  Returns *self*."""
        self._sources.append(source)
        return self

    def stream(self) -> Iterator[dict]:
        """Yield all entries from all sources in sorted order."""
        if not self._sources:
            return

        # heapq.merge requires comparable items; wrap each entry so that
        # missing keys sort last and dict comparison is avoided.
        iterators = [self._keyed(src) for src in self._sources]
        for _sort_key, _source_idx, entry in heapq.merge(*iterators):
            yield entry

    def collect(self) -> List[dict]:
        """Return all merged entries as a list."""
        return list(self.stream())

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _keyed(
        self, source: Iterable[dict]
    ) -> Iterator[Tuple[Tuple, int, dict]]:
        """Wrap each entry with a comparable sort tuple for heapq.merge."""
        for idx, entry in enumerate(source):
            raw = self._key_fn(entry)
            # Entries without a timestamp sort last; use a two-element tuple
            # so that (False, value) < (True, "") keeps timestamped first.
            missing = raw == "" or raw is None
            sort_key = (missing, raw if not missing else "", idx)
            yield sort_key, idx, entry
