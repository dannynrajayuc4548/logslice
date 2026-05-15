"""LogPartitioner – split a stream of log entries into time-based partitions."""
from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from typing import Callable, Dict, Iterable, List, Optional

_GRANULARITIES = ("hour", "day", "month", "year")


def _default_key(entry: dict, granularity: str, ts_field: str) -> str:
    raw = entry.get(ts_field, "")
    if not raw:
        return "unknown"
    try:
        if isinstance(raw, datetime):
            dt = raw
        else:
            dt = datetime.fromisoformat(str(raw))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        if granularity == "hour":
            return dt.strftime("%Y-%m-%dT%H")
        if granularity == "day":
            return dt.strftime("%Y-%m-%d")
        if granularity == "month":
            return dt.strftime("%Y-%m")
        if granularity == "year":
            return dt.strftime("%Y")
    except (ValueError, TypeError):
        return "unknown"
    return "unknown"


class LogPartitioner:
    """Partition log entries by a time granularity or a custom key function."""

    def __init__(
        self,
        granularity: str = "day",
        ts_field: str = "timestamp",
        key_fn: Optional[Callable[[dict], str]] = None,
    ) -> None:
        if granularity not in _GRANULARITIES:
            raise ValueError(
                f"granularity must be one of {_GRANULARITIES}, got {granularity!r}"
            )
        if not ts_field or not ts_field.strip():
            raise ValueError("ts_field must be a non-empty string")
        self._granularity = granularity
        self._ts_field = ts_field
        self._key_fn: Callable[[dict], str] = key_fn or (
            lambda e: _default_key(e, self._granularity, self._ts_field)
        )
        self._buckets: Dict[str, List[dict]] = defaultdict(list)

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def granularity(self) -> str:
        return self._granularity

    @property
    def ts_field(self) -> str:
        return self._ts_field

    @property
    def buckets(self) -> Dict[str, List[dict]]:
        return dict(self._buckets)

    @property
    def partition_keys(self) -> List[str]:
        return sorted(self._buckets.keys())

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def feed(self, entries: Iterable[dict]) -> "LogPartitioner":
        """Feed an iterable of entries into the partitioner."""
        for entry in entries:
            key = self._key_fn(entry)
            self._buckets[key].append(entry)
        return self

    def get(self, key: str) -> List[dict]:
        """Return all entries for a given partition key (empty list if missing)."""
        return list(self._buckets.get(key, []))

    def reset(self) -> "LogPartitioner":
        """Clear all accumulated partitions."""
        self._buckets.clear()
        return self
