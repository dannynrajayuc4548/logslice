"""LogSorter – sort a stream of log entries by a field value."""
from __future__ import annotations

from typing import Any, Callable, Iterable, Iterator, List, Optional


_MISSING = object()


class LogSorter:
    """Collect log entries and yield them sorted by a chosen field.

    Parameters
    ----------
    field:
        The entry key to sort by.  Defaults to ``"timestamp"``.
    default:
        Value used when the key is absent.  Defaults to ``""``.
    reverse:
        If ``True``, sort in descending order.
    key:
        Optional callable that transforms the field value before comparison.
    """

    def __init__(
        self,
        field: str = "timestamp",
        *,
        default: Any = "",
        reverse: bool = False,
        key: Optional[Callable[[Any], Any]] = None,
    ) -> None:
        if not field or not field.strip():
            raise ValueError("field must be a non-empty string")
        self._field = field
        self._default = default
        self._reverse = reverse
        self._key: Callable[[Any], Any] = key if key is not None else (lambda v: v)

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def field(self) -> str:
        return self._field

    @property
    def default(self) -> Any:
        return self._default

    @property
    def reverse(self) -> bool:
        return self._reverse

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def sort(self, entries: Iterable[dict]) -> List[dict]:
        """Return a new list with *entries* sorted by the configured field."""
        items = list(entries)
        items.sort(
            key=lambda e: self._key(e.get(self._field, self._default)),
            reverse=self._reverse,
        )
        return items

    def stream(self, entries: Iterable[dict]) -> Iterator[dict]:
        """Yield entries in sorted order (buffers all input first)."""
        yield from self.sort(entries)
