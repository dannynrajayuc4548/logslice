"""Log aggregation utilities for grouping and counting log entries."""

from collections import defaultdict
from typing import Any, Callable, Dict, Iterable, List, Optional


class LogAggregator:
    """Aggregates parsed log entries by a specified key or function."""

    def __init__(self, key: str = "level", transform: Optional[Callable[[Any], Any]] = None):
        """
        Args:
            key: The field name in each log entry dict to group by.
            transform: Optional callable to transform the key value before grouping.
        """
        self.key = key
        self.transform = transform
        self._buckets: Dict[Any, List[dict]] = defaultdict(list)

    def feed(self, entries: Iterable[dict]) -> None:
        """Feed an iterable of parsed log entry dicts into the aggregator."""
        for entry in entries:
            raw_value = entry.get(self.key, "__unknown__")
            bucket_key = self.transform(raw_value) if self.transform else raw_value
            self._buckets[bucket_key].append(entry)

    def groups(self) -> Dict[Any, List[dict]]:
        """Return a dict mapping each group key to a list of matching entries."""
        return dict(self._buckets)

    def counts(self) -> Dict[Any, int]:
        """Return a dict mapping each group key to the number of entries."""
        return {k: len(v) for k, v in self._buckets.items()}

    def top(self, n: int = 5) -> List[tuple]:
        """Return the top-n groups by entry count as (key, count) pairs."""
        sorted_counts = sorted(self.counts().items(), key=lambda x: x[1], reverse=True)
        return sorted_counts[:n]

    def reset(self) -> None:
        """Clear all accumulated data."""
        self._buckets = defaultdict(list)
