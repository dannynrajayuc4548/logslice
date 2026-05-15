"""LogCapper – limit the total number of log entries yielded from any iterable."""
from __future__ import annotations

from typing import Iterable, Iterator


class LogCapper:
    """Yield at most *limit* entries from a stream.

    Parameters
    ----------
    limit:
        Maximum number of entries to pass through.  Must be a positive integer.
    skip:
        Number of entries to discard from the *start* of the stream before
        beginning to yield.  Defaults to ``0``.
    """

    def __init__(self, limit: int, *, skip: int = 0) -> None:
        if not isinstance(limit, int) or limit < 1:
            raise ValueError("limit must be a positive integer")
        if not isinstance(skip, int) or skip < 0:
            raise ValueError("skip must be a non-negative integer")
        self._limit = limit
        self._skip = skip

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def limit(self) -> int:
        """Maximum number of entries to yield."""
        return self._limit

    @property
    def skip(self) -> int:
        """Number of leading entries to discard."""
        return self._skip

    # ------------------------------------------------------------------
    # Core API
    # ------------------------------------------------------------------

    def stream(self, entries: Iterable[dict]) -> Iterator[dict]:
        """Yield up to *limit* entries after skipping the first *skip* items."""
        seen = 0
        yielded = 0
        for entry in entries:
            if seen < self._skip:
                seen += 1
                continue
            if yielded >= self._limit:
                break
            yield entry
            yielded += 1

    def collect(self, entries: Iterable[dict]) -> list[dict]:
        """Return a list of at most *limit* entries."""
        return list(self.stream(entries))
