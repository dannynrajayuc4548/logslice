"""FormatterPipeline — convenience wrapper that couples a LogPipeline with a
specific formatter so that every collected entry is rendered consistently."""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional, Type

from .pipeline import LogPipeline
from .formatters import BaseFormatter, JSONFormatter, PlainFormatter


class FormatterPipeline:
    """Run a LogPipeline and render each result through a chosen formatter.

    Parameters
    ----------
    path:
        Path to the JSONL log file to process.
    formatter:
        A :class:`~logslice.formatters.BaseFormatter` instance.  Defaults to
        :class:`~logslice.formatters.JSONFormatter`.
    """

    def __init__(
        self,
        path: str,
        formatter: Optional[BaseFormatter] = None,
    ) -> None:
        self._pipeline: LogPipeline = LogPipeline(path)
        self._formatter: BaseFormatter = formatter if formatter is not None else JSONFormatter()

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def pipeline(self) -> LogPipeline:
        """The underlying :class:`~logslice.pipeline.LogPipeline`."""
        return self._pipeline

    @property
    def formatter(self) -> BaseFormatter:
        """The active :class:`~logslice.formatters.BaseFormatter`."""
        return self._formatter

    # ------------------------------------------------------------------
    # Fluent helpers
    # ------------------------------------------------------------------

    def add_filter(self, f: Any) -> "FormatterPipeline":
        """Delegate a filter to the underlying pipeline and return *self*."""
        self._pipeline.add_filter(f)
        return self

    def set_formatter(self, formatter: BaseFormatter) -> "FormatterPipeline":
        """Replace the active formatter and return *self*."""
        if not isinstance(formatter, BaseFormatter):
            raise TypeError("formatter must be a BaseFormatter instance")
        self._formatter = formatter
        return self

    # ------------------------------------------------------------------
    # Output
    # ------------------------------------------------------------------

    def render(self) -> List[str]:
        """Return every matching entry rendered as a string."""
        return [self._formatter.format(entry) for entry in self._pipeline.collect()]

    def stream_rendered(self) -> Iterable[str]:
        """Yield each matching entry rendered as a string."""
        for entry in self._pipeline.collect():
            yield self._formatter.format(entry)
