"""LogPipeline: fluent end-to-end log processing pipeline."""

from typing import Any, Dict, Iterable, Iterator, List, Optional

from logslice.enricher import LogEnricher
from logslice.filters import BaseFilter, RegexFilter, TimeRangeFilter
from logslice.formatters import BaseFormatter
from logslice.parser import LogParser


class LogPipeline:
    """Fluent builder that chains parsing → filtering → enrichment → formatting.

    Example::

        results = (
            LogPipeline("app.log")
            .add_filter(RegexFilter("error"))
            .enrich("env", "prod")
            .set_formatter(JSONFormatter())
            .run()
        )
    """

    def __init__(self, path: str) -> None:
        self._path = path
        self._filters: List[BaseFilter] = []
        self._formatter: Optional[BaseFormatter] = None
        self._enricher: LogEnricher = LogEnricher()
        self._field: str = "message"

    # ------------------------------------------------------------------
    # Builder methods
    # ------------------------------------------------------------------

    def add_filter(self, f: BaseFilter) -> "LogPipeline":
        """Append a filter; returns *self* for chaining."""
        self._filters.append(f)
        return self

    def set_formatter(self, formatter: BaseFormatter) -> "LogPipeline":
        """Set the output formatter; returns *self* for chaining."""
        self._formatter = formatter
        return self

    def enrich(self, key: str, value: Any) -> "LogPipeline":
        """Register an enrichment rule; returns *self* for chaining."""
        self._enricher.add(key, value)
        return self

    def set_field(self, field: str) -> "LogPipeline":
        """Set the default field used by filters (default: 'message')."""
        self._field = field
        return self

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _build_parser(self) -> LogParser:
        parser = LogParser(self._path)
        for f in self._filters:
            parser.add_filter(f)
        return parser

    def _iter_entries(self) -> Iterator[Dict[str, Any]]:
        parser = self._build_parser()
        for entry in parser.stream():
            yield self._enricher.apply(entry)

    # ------------------------------------------------------------------
    # Terminal operations
    # ------------------------------------------------------------------

    def run(self) -> List[Any]:
        """Collect all processed entries into a list."""
        results = []
        for entry in self._iter_entries():
            if self._formatter:
                results.append(self._formatter.format(entry))
            else:
                results.append(entry)
        return results

    def stream(self) -> Iterator[Any]:
        """Lazily yield processed entries."""
        for entry in self._iter_entries():
            if self._formatter:
                yield self._formatter.format(entry)
            else:
                yield entry
