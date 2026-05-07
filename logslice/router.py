"""Route log entries to different handlers based on field values or filters."""

from typing import Callable, Dict, List, Optional, Tuple
from logslice.filters import BaseFilter


class LogRouter:
    """Routes parsed log entries to named buckets based on filter rules.

    Rules are evaluated in order; the first matching rule wins.
    An optional fallback bucket captures unmatched entries.
    """

    def __init__(self, fallback: str = "default") -> None:
        self._fallback = fallback
        self._rules: List[Tuple[str, BaseFilter]] = []
        self._buckets: Dict[str, List[dict]] = {}
        self._callbacks: Dict[str, List[Callable[[dict], None]]] = {}

    def add_rule(self, bucket: str, filter_: BaseFilter) -> "LogRouter":
        """Register a filter; matching entries go to *bucket*."""
        self._rules.append((bucket, filter_))
        return self

    def on(self, bucket: str, callback: Callable[[dict], None]) -> "LogRouter":
        """Attach a callback invoked whenever an entry lands in *bucket*."""
        self._callbacks.setdefault(bucket, []).append(callback)
        return self

    def route(self, entry: dict) -> str:
        """Route a single entry and return the bucket name it was sent to."""
        for bucket, filter_ in self._rules:
            if filter_.match(entry):
                self._dispatch(bucket, entry)
                return bucket
        self._dispatch(self._fallback, entry)
        return self._fallback

    def route_many(self, entries) -> Dict[str, List[dict]]:
        """Route an iterable of entries and return the populated buckets."""
        for entry in entries:
            self.route(entry)
        return self.buckets

    def _dispatch(self, bucket: str, entry: dict) -> None:
        self._buckets.setdefault(bucket, []).append(entry)
        for cb in self._callbacks.get(bucket, []):
            cb(entry)

    @property
    def buckets(self) -> Dict[str, List[dict]]:
        """Return a snapshot of all collected buckets."""
        return dict(self._buckets)

    def bucket(self, name: str) -> List[dict]:
        """Return entries for a single named bucket (empty list if none)."""
        return self._buckets.get(name, [])

    def clear(self) -> None:
        """Discard all collected entries (rules and callbacks are kept)."""
        self._buckets.clear()
