"""LogSampler — rate-based and reservoir sampling for log entry streams."""

import random
from typing import Callable, Iterable, Iterator, List, Optional


class LogSampler:
    """Sample log entries from an iterable stream.

    Supports two strategies:
      - ``rate``: keep each entry independently with probability *rate* (0.0-1.0).
      - ``reservoir``: return exactly *size* entries chosen uniformly at random
        (reservoir sampling, Algorithm R).
    """

    def __init__(
        self,
        rate: Optional[float] = None,
        reservoir_size: Optional[int] = None,
        seed: Optional[int] = None,
        transform: Optional[Callable[[dict], dict]] = None,
    ) -> None:
        if rate is not None and not (0.0 <= rate <= 1.0):
            raise ValueError("rate must be between 0.0 and 1.0")
        if reservoir_size is not None and reservoir_size < 1:
            raise ValueError("reservoir_size must be a positive integer")
        if rate is None and reservoir_size is None:
            raise ValueError("Provide either 'rate' or 'reservoir_size'")
        if rate is not None and reservoir_size is not None:
            raise ValueError("Provide only one of 'rate' or 'reservoir_size'")

        self._rate = rate
        self._reservoir_size = reservoir_size
        self._rng = random.Random(seed)
        self._transform = transform

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def sample(self, entries: Iterable[dict]) -> List[dict]:
        """Return a sampled list from *entries*."""
        if self._rate is not None:
            return list(self._rate_sample(entries))
        return self._reservoir_sample(entries)

    def stream(self, entries: Iterable[dict]) -> Iterator[dict]:
        """Yield sampled entries one by one (rate mode only).

        For reservoir mode use :meth:`sample` instead.
        """
        if self._rate is None:
            raise RuntimeError("stream() is only supported in rate mode; use sample() for reservoir mode")
        yield from self._rate_sample(entries)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _apply(self, entry: dict) -> dict:
        if self._transform is not None:
            return self._transform(entry)
        return entry

    def _rate_sample(self, entries: Iterable[dict]) -> Iterator[dict]:
        for entry in entries:
            if self._rng.random() < self._rate:  # type: ignore[operator]
                yield self._apply(entry)

    def _reservoir_sample(self, entries: Iterable[dict]) -> List[dict]:
        size = self._reservoir_size  # type: ignore[assignment]
        reservoir: List[dict] = []
        for i, entry in enumerate(entries):
            if i < size:
                reservoir.append(self._apply(entry))
            else:
                j = self._rng.randint(0, i)
                if j < size:
                    reservoir[j] = self._apply(entry)
        return reservoir
