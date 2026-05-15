"""DiffPipeline – convenience wrapper that runs two log files through LogDiffer."""
from __future__ import annotations

from typing import Any, Callable, Dict, Iterator, List, Tuple

from logslice.differ import LogDiffer
from logslice.pipeline import LogPipeline

_Entry = Dict[str, Any]


class DiffPipeline:
    """Parse two log files, apply optional filters, then diff the results.

    Parameters
    ----------
    left_path:
        Path to the *baseline* log file.
    right_path:
        Path to the *comparison* log file.
    key:
        Identity function forwarded to :class:`~logslice.differ.LogDiffer`.
    compare_fields:
        Field restriction forwarded to :class:`~logslice.differ.LogDiffer`.
    """

    def __init__(
        self,
        left_path: str,
        right_path: str,
        key: Callable[[_Entry], str] | None = None,
        compare_fields: List[str] | None = None,
    ) -> None:
        self._left_pipeline = LogPipeline(left_path)
        self._right_pipeline = LogPipeline(right_path)
        self._differ = LogDiffer(key=key, compare_fields=compare_fields)

    # ------------------------------------------------------------------
    # public accessors
    # ------------------------------------------------------------------

    @property
    def left_pipeline(self) -> LogPipeline:
        return self._left_pipeline

    @property
    def right_pipeline(self) -> LogPipeline:
        return self._right_pipeline

    @property
    def differ(self) -> LogDiffer:
        return self._differ

    # ------------------------------------------------------------------
    # filter delegation
    # ------------------------------------------------------------------

    def add_filter(self, f: Any, *, side: str = "both") -> "DiffPipeline":
        """Add a filter to one or both pipelines.

        Parameters
        ----------
        f:
            Any filter accepted by :meth:`LogPipeline.add_filter`.
        side:
            ``'left'``, ``'right'``, or ``'both'`` (default).
        """
        if side in ("left", "both"):
            self._left_pipeline.add_filter(f)
        if side in ("right", "both"):
            self._right_pipeline.add_filter(f)
        return self

    # ------------------------------------------------------------------
    # execution
    # ------------------------------------------------------------------

    def run(self, *, only_changes: bool = False) -> Iterator[Tuple[str, _Entry]]:
        """Execute both pipelines and yield diff tuples.

        Parameters
        ----------
        only_changes:
            When *True* suppress ``'unchanged'`` entries.
        """
        left = list(self._left_pipeline.run())
        right = list(self._right_pipeline.run())
        if only_changes:
            yield from self._differ.only_changes(left, right)
        else:
            yield from self._differ.diff(left, right)

    def counts(self, *, only_changes: bool = False) -> Dict[str, int]:
        """Return a summary dict mapping status → count."""
        tally: Dict[str, int] = {}
        for status, _ in self.run(only_changes=only_changes):
            tally[status] = tally.get(status, 0) + 1
        return tally
