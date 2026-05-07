"""Rate limiter for log entry streams — limits throughput to N entries per second."""

import time
from collections import deque
from typing import Iterable, Iterator, Optional


class LogRateLimiter:
    """Limits the rate at which log entries are yielded from a stream.

    Uses a token-bucket-style approach: if the inter-entry delay would exceed
    the allowed rate, the iterator sleeps before yielding the next entry.

    Args:
        rate (float): Maximum number of entries to yield per second.
        burst (int): Maximum burst size (entries that may be yielded instantly
            before throttling kicks in). Defaults to 1.
    """

    def __init__(self, rate: float, burst: int = 1) -> None:
        if rate <= 0:
            raise ValueError(f"rate must be positive, got {rate!r}")
        if burst < 1:
            raise ValueError(f"burst must be >= 1, got {burst!r}")
        self._rate = rate
        self._burst = burst
        # Track timestamps of recent emissions for sliding-window accounting
        self._window: deque = deque()

    @property
    def rate(self) -> float:
        return self._rate

    @property
    def burst(self) -> int:
        return self._burst

    def stream(
        self,
        entries: Iterable[dict],
        *,
        _sleep=time.sleep,
        _now=time.monotonic,
    ) -> Iterator[dict]:
        """Yield entries from *entries* at most ``rate`` entries per second.

        Args:
            entries: Any iterable of log-entry dicts.
            _sleep: Injectable sleep callable (for testing).
            _now: Injectable monotonic clock (for testing).

        Yields:
            dict: The next log entry, after honouring the rate limit.
        """
        interval = 1.0 / self._rate
        window = self._window
        window.clear()

        for entry in entries:
            now = _now()
            # Evict timestamps outside the 1-second sliding window
            cutoff = now - 1.0
            while window and window[0] <= cutoff:
                window.popleft()

            if len(window) >= self._burst:
                # Must wait until the oldest slot falls outside the window
                wait_until = window[0] + 1.0
                delay = wait_until - _now()
                if delay > 0:
                    _sleep(delay)
                now = _now()
                # Re-evict after sleeping
                cutoff = now - 1.0
                while window and window[0] <= cutoff:
                    window.popleft()

            window.append(_now())
            yield entry
