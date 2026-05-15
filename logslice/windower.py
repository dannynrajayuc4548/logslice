"""Sliding and tumbling window aggregation over log entry streams."""

from __future__ import annotations

from collections import deque
from typing import Callable, Dict, Iterable, Iterator, List, Optional


class LogWindower:
    """Group log entries into fixed-size or sliding windows.

    Parameters
    ----------
    size:
        Number of entries per window.
    step:
        How many entries to advance before starting the next window.
        ``step == size`` gives tumbling (non-overlapping) windows.
        ``step < size`` gives sliding (overlapping) windows.
        Defaults to *size* (tumbling).
    ts_field:
        If provided, windows are keyed by the value of this field taken
        from the *first* entry in the window.
    """

    def __init__(
        self,
        size: int,
        step: Optional[int] = None,
        ts_field: Optional[str] = None,
    ) -> None:
        if size < 1:
            raise ValueError("size must be >= 1")
        _step = size if step is None else step
        if _step < 1:
            raise ValueError("step must be >= 1")
        if _step > size:
            raise ValueError("step must be <= size")
        self._size = size
        self._step = _step
        self._ts_field = ts_field

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def size(self) -> int:
        return self._size

    @property
    def step(self) -> int:
        return self._step

    @property
    def ts_field(self) -> Optional[str]:
        return self._ts_field

    # ------------------------------------------------------------------
    # Core API
    # ------------------------------------------------------------------

    def windows(
        self, entries: Iterable[Dict]
    ) -> Iterator[Dict]:
        """Yield window dicts with keys ``entries``, ``count``, and
        optionally ``ts`` (value of *ts_field* from the first entry)."""
        buf: deque = deque()
        emitted = 0

        for entry in entries:
            buf.append(entry)
            if len(buf) == self._size:
                window_entries = list(buf)
                result: Dict = {
                    "entries": window_entries,
                    "count": len(window_entries),
                }
                if self._ts_field:
                    result["ts"] = window_entries[0].get(self._ts_field)
                yield result
                for _ in range(self._step):
                    if buf:
                        buf.popleft()

    def collect(self, entries: Iterable[Dict]) -> List[Dict]:
        """Return all windows as a list."""
        return list(self.windows(entries))
