"""PivotPipeline – convenience wrapper combining LogPipeline with LogPivot."""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional

from .pipeline import LogPipeline
from .pivot import LogPivot


class PivotPipeline:
    """Read a log file through a :class:`LogPipeline`, then feed results into
    a :class:`LogPivot` to produce a pivot table in one fluent call.

    Example::

        table = (
            PivotPipeline("app.log", row_field="host", col_field="level")
            .add_filter(RegexFilter("error|warn"))
            .run()
        )
    """

    def __init__(
        self,
        path: str,
        row_field: str = "host",
        col_field: str = "level",
        value_field: Optional[str] = None,
        agg: Optional[Callable[[Any, Dict], Any]] = None,
        default_row: str = "unknown",
        default_col: str = "unknown",
    ) -> None:
        self._pipeline = LogPipeline(path)
        self._pivot = LogPivot(
            row_field=row_field,
            col_field=col_field,
            value_field=value_field,
            agg=agg,
            default_row=default_row,
            default_col=default_col,
        )

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def pipeline(self) -> LogPipeline:
        return self._pipeline

    @property
    def pivot(self) -> LogPivot:
        return self._pivot

    # ------------------------------------------------------------------
    # Fluent configuration
    # ------------------------------------------------------------------

    def add_filter(self, f) -> "PivotPipeline":
        self._pipeline.add_filter(f)
        return self

    def enrich(self, key: str, value) -> "PivotPipeline":
        self._pipeline.enrich(key, value)
        return self

    # ------------------------------------------------------------------
    # Execution
    # ------------------------------------------------------------------

    def run(self, fill: Any = 0) -> List[Dict[str, Any]]:
        """Execute the pipeline, feed entries into the pivot and return the
        pivot table (list of row dicts).
        """
        entries = self._pipeline.collect()
        self._pivot.feed(entries)
        return self._pivot.table(fill=fill)

    def columns(self) -> List[str]:
        """Columns discovered after :meth:`run` has been called."""
        return self._pivot.columns()

    def rows(self) -> List[str]:
        """Row keys discovered after :meth:`run` has been called."""
        return self._pivot.rows()
