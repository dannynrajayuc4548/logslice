"""SortPipeline – convenience wrapper that combines LogPipeline with LogSorter."""
from __future__ import annotations

from typing import Any, Callable, Iterator, List, Optional

from .pipeline import LogPipeline
from .sorter import LogSorter


class SortPipeline:
    """Filter a log file and yield entries sorted by a field.

    Example
    -------
    >>> sp = SortPipeline("app.log", field="timestamp")
    >>> sp.add_filter(RegexFilter("ERROR"))
    >>> for entry in sp.stream():
    ...     print(entry)
    """

    def __init__(
        self,
        path: str,
        *,
        field: str = "timestamp",
        default: Any = "",
        reverse: bool = False,
        key: Optional[Callable[[Any], Any]] = None,
    ) -> None:
        self._pipeline = LogPipeline(path)
        self._sorter = LogSorter(
            field=field, default=default, reverse=reverse, key=key
        )

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def pipeline(self) -> LogPipeline:
        return self._pipeline

    @property
    def sorter(self) -> LogSorter:
        return self._sorter

    # ------------------------------------------------------------------
    # Delegation helpers
    # ------------------------------------------------------------------

    def add_filter(self, f: Any) -> "SortPipeline":
        self._pipeline.add_filter(f)
        return self

    def set_formatter(self, formatter: Any) -> "SortPipeline":
        self._pipeline.set_formatter(formatter)
        return self

    # ------------------------------------------------------------------
    # Output
    # ------------------------------------------------------------------

    def stream(self) -> Iterator[dict]:
        """Yield all matching entries in sorted order."""
        yield from self._sorter.stream(self._pipeline.stream())

    def collect(self) -> List[dict]:
        """Return all matching entries as a sorted list."""
        return self._sorter.sort(self._pipeline.stream())
