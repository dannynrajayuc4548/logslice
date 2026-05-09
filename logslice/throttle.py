"""LogThrottle: suppress repeated log entries within a sliding time window."""

from __future__ import annotations

import time
from collections import defaultdict
from typing import Callable, Dict, Iterable, Iterator, Optional, Tuple


def _default_key(entry: dict) -> str:
    """Build a dedup key from level + message (or raw)."""
    level = entry.get("level", "")
    message = entry.get("message", entry.get("msg", entry.get("raw", "")))
    return f"{level}::{message}"


class LogThrottle:
    """Suppress log entries whose key has been seen within *window* seconds.

    Parameters
    ----------
    window:
        Silence period in seconds.  Duplicate entries arriving within this
        window after the first occurrence are dropped.
    key_fn:
        Callable that accepts an entry dict and returns a hashable key used
        to identify "the same" event.  Defaults to ``level + message``.
    clock:
        Callable that returns the current time as a float (seconds).  Useful
        for testing; defaults to :func:`time.monotonic`.
    """

    def __init__(
        self,
        window: float,
        key_fn: Optional[Callable[[dict], str]] = None,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        if window < 0:
            raise ValueError("window must be >= 0")
        self._window = window
        self._key_fn = key_fn or _default_key
        self._clock = clock
        # key -> timestamp of first occurrence in current window
        self._seen: Dict[str, float] = {}
        self._suppressed: int = 0
        self._passed: int = 0

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def window(self) -> float:
        return self._window

    @property
    def suppressed(self) -> int:
        """Total entries suppressed since creation."""
        return self._suppressed

    @property
    def passed(self) -> int:
        """Total entries allowed through since creation."""
        return self._passed

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def allow(self, entry: dict) -> bool:
        """Return True if *entry* should be forwarded, False if suppressed."""
        key = self._key_fn(entry)
        now = self._clock()
        last = self._seen.get(key)
        if last is None or (now - last) >= self._window:
            self._seen[key] = now
            self._passed += 1
            return True
        self._suppressed += 1
        return False

    def stream(self, entries: Iterable[dict]) -> Iterator[dict]:
        """Yield only entries that pass the throttle."""
        for entry in entries:
            if self.allow(entry):
                yield entry

    def reset(self) -> None:
        """Clear all remembered keys (does not reset counters)."""
        self._seen.clear()
