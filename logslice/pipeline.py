"""Pipeline: chain filters, a formatter, and a writer into a single pass."""

from __future__ import annotations

from typing import Iterable, List, Optional

from .filters import BaseFilter
from .formatters import BaseFormatter, PlainFormatter
from .parser import LogParser
from .writer import LogWriter


class LogPipeline:
    """High-level helper that wires a parser, filters, formatter, and writer.

    Example::

        pipeline = LogPipeline()
        pipeline.add_filter(RegexFilter("error"))
        pipeline.set_formatter(JSONFormatter())
        results = pipeline.run_file("app.log")
    """

    def __init__(
        self,
        formatter: Optional[BaseFormatter] = None,
        writer: Optional[LogWriter] = None,
    ) -> None:
        self._filters: List[BaseFilter] = []
        self._formatter: BaseFormatter = formatter or PlainFormatter()
        self._writer: LogWriter = writer or LogWriter(formatter=self._formatter)

    # ------------------------------------------------------------------
    # Configuration helpers
    # ------------------------------------------------------------------

    def add_filter(self, f: BaseFilter) -> "LogPipeline":
        """Append a filter and return *self* for chaining."""
        self._filters.append(f)
        return self

    def set_formatter(self, formatter: BaseFormatter) -> "LogPipeline":
        """Replace the current formatter (also updates the writer)."""
        self._formatter = formatter
        self._writer = LogWriter(formatter=formatter)
        return self

    # ------------------------------------------------------------------
    # Execution
    # ------------------------------------------------------------------

    def _build_parser(self) -> LogParser:
        parser = LogParser()
        for f in self._filters:
            parser.add_filter(f)
        return parser

    def run(self, lines: Iterable[str]) -> List[str]:
        """Process an iterable of raw log lines and return formatted strings."""
        parser = self._build_parser()
        entries = list(parser.stream(lines))
        for entry in entries:
            self._writer.write(entry)
        return self._writer.collect()

    def run_file(self, path: str) -> List[str]:
        """Open *path*, run the pipeline, and return formatted strings."""
        with open(path, "r", encoding="utf-8") as fh:
            return self.run(fh)
