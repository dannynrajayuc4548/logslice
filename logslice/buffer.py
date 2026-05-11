"""LogBuffer — accumulate log entries in memory with optional capacity and flush support.

Useful when you want to batch entries before writing, exporting, or processing
them as a group rather than one at a time.
"""

from __future__ import annotations

from collections import deque
from typing import Callable, Deque, Dict, Iterable, Iterator, List, Optional


class BufferFullError(Exception):
    """Raised when an entry is fed into a full buffer and overflow is not allowed."""


class LogBuffer:
    """In-memory ring-buffer for log entries.

    Parameters
    ----------
    capacity:
        Maximum number of entries to hold.  ``None`` means unlimited.
    on_flush:
        Optional callback invoked with the list of entries each time the buffer
        is flushed.  Useful for side-effects such as writing to disk.
    overflow:
        Strategy when *capacity* is exceeded.  ``'drop'`` silently discards the
        oldest entry; ``'raise'`` raises :class:`BufferFullError`.
    """

    def __init__(
        self,
        capacity: Optional[int] = None,
        on_flush: Optional[Callable[[List[Dict]], None]] = None,
        overflow: str = "drop",
    ) -> None:
        if capacity is not None and capacity < 1:
            raise ValueError("capacity must be a positive integer or None")
        if overflow not in ("drop", "raise"):
            raise ValueError("overflow must be 'drop' or 'raise'")

        self._capacity = capacity
        self._on_flush = on_flush
        self._overflow = overflow
        self._buf: Deque[Dict] = deque()
        self._total_fed: int = 0
        self._total_dropped: int = 0

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def capacity(self) -> Optional[int]:
        """Maximum capacity, or ``None`` if unlimited."""
        return self._capacity

    @property
    def overflow(self) -> str:
        """Overflow strategy: ``'drop'`` or ``'raise'``."""
        return self._overflow

    @property
    def size(self) -> int:
        """Number of entries currently held."""
        return len(self._buf)

    @property
    def is_full(self) -> bool:
        """``True`` when the buffer has reached its capacity."""
        return self._capacity is not None and len(self._buf) >= self._capacity

    @property
    def total_fed(self) -> int:
        """Total entries ever fed into this buffer (including dropped ones)."""
        return self._total_fed

    @property
    def total_dropped(self) -> int:
        """Total entries silently dropped due to overflow."""
        return self._total_dropped

    # ------------------------------------------------------------------
    # Core API
    # ------------------------------------------------------------------

    def feed(self, entry: Dict) -> "LogBuffer":
        """Add *entry* to the buffer.

        If the buffer is full and *overflow* is ``'raise'``, a
        :class:`BufferFullError` is raised.  If *overflow* is ``'drop'``,
        the oldest entry is silently removed to make room.

        Returns *self* for chaining.
        """
        self._total_fed += 1
        if self._capacity is not None and len(self._buf) >= self._capacity:
            if self._overflow == "raise":
                raise BufferFullError(
                    f"Buffer is full (capacity={self._capacity})"
                )
            # drop oldest
            self._buf.popleft()
            self._total_dropped += 1
        self._buf.append(entry)
        return self

    def feed_many(self, entries: Iterable[Dict]) -> "LogBuffer":
        """Feed multiple entries, returning *self* for chaining."""
        for entry in entries:
            self.feed(entry)
        return self

    def flush(self) -> List[Dict]:
        """Return all buffered entries and clear the buffer.

        If an *on_flush* callback was provided it is called with the list
        before returning.
        """
        entries = list(self._buf)
        self._buf.clear()
        if self._on_flush is not None:
            self._on_flush(entries)
        return entries

    def peek(self) -> List[Dict]:
        """Return a snapshot of the current entries without clearing."""
        return list(self._buf)

    def clear(self) -> "LogBuffer":
        """Discard all buffered entries without triggering *on_flush*."""
        self._buf.clear()
        return self

    def __iter__(self) -> Iterator[Dict]:
        """Iterate over buffered entries without consuming them."""
        return iter(list(self._buf))

    def __len__(self) -> int:
        return len(self._buf)

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"LogBuffer(size={self.size}, capacity={self._capacity}, "
            f"overflow={self._overflow!r})"
        )
