"""LogProfiler – collect timing and throughput statistics over a log stream."""
from __future__ import annotations

import time
from typing import Callable, Dict, Iterable, Iterator, List, Optional


class LogProfiler:
    """Measure processing throughput and per-field value latency for log entries.

    Parameters
    ----------
    timestamp_field:
        Entry key that holds an epoch-float (or parseable float) timestamp.
        When supplied, inter-event latency is tracked.  Defaults to ``None``.
    clock:
        Callable returning the current wall time as a float.  Defaults to
        ``time.monotonic``.  Useful for deterministic testing.
    """

    def __init__(
        self,
        timestamp_field: Optional[str] = None,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        if timestamp_field is not None and not str(timestamp_field).strip():
            raise ValueError("timestamp_field must not be blank")
        self._ts_field = timestamp_field
        self._clock = clock
        self._count: int = 0
        self._start: Optional[float] = None
        self._end: Optional[float] = None
        self._latencies: List[float] = []
        self._prev_event_ts: Optional[float] = None

    # ------------------------------------------------------------------
    # properties
    # ------------------------------------------------------------------

    @property
    def count(self) -> int:
        """Total number of entries processed."""
        return self._count

    @property
    def elapsed(self) -> float:
        """Wall-clock seconds between first and last *feed* call."""
        if self._start is None:
            return 0.0
        end = self._end if self._end is not None else self._clock()
        return max(0.0, end - self._start)

    @property
    def throughput(self) -> float:
        """Entries per second; 0.0 when elapsed is zero."""
        e = self.elapsed
        return self._count / e if e > 0 else 0.0

    @property
    def latencies(self) -> List[float]:
        """Copy of inter-event latency samples (seconds) derived from *timestamp_field*."""
        return list(self._latencies)

    @property
    def mean_latency(self) -> Optional[float]:
        """Mean inter-event latency, or *None* when no samples exist."""
        if not self._latencies:
            return None
        return sum(self._latencies) / len(self._latencies)

    # ------------------------------------------------------------------
    # public API
    # ------------------------------------------------------------------

    def feed(self, entry: Dict) -> Dict:
        """Record *entry* and return it unchanged."""
        now = self._clock()
        if self._start is None:
            self._start = now
        self._end = now
        self._count += 1

        if self._ts_field and self._ts_field in entry:
            try:
                ts = float(entry[self._ts_field])
                if self._prev_event_ts is not None:
                    delta = ts - self._prev_event_ts
                    if delta >= 0:
                        self._latencies.append(delta)
                self._prev_event_ts = ts
            except (TypeError, ValueError):
                pass

        return entry

    def stream(self, entries: Iterable[Dict]) -> Iterator[Dict]:
        """Wrap an iterable, feeding each entry through the profiler."""
        for entry in entries:
            yield self.feed(entry)

    def reset(self) -> None:
        """Clear all accumulated statistics."""
        self._count = 0
        self._start = None
        self._end = None
        self._latencies.clear()
        self._prev_event_ts = None

    def summary(self) -> Dict:
        """Return a plain-dict snapshot of current statistics."""
        return {
            "count": self._count,
            "elapsed": self.elapsed,
            "throughput": self.throughput,
            "mean_latency": self.mean_latency,
            "latency_samples": len(self._latencies),
        }
