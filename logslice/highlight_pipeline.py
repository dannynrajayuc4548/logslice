"""Convenience pipeline that combines LogPipeline with LogHighlighter."""
from typing import Any, Callable, Dict, Iterable, List, Optional

from .pipeline import LogPipeline
from .highlighter import LogHighlighter


class HighlightPipeline:
    """Filter log entries and annotate matches with highlight metadata.

    Example::

        pipe = (
            HighlightPipeline("app.log")
            .add_rule("message", r"ERROR", re.IGNORECASE)
            .add_rule("message", r"timeout")
        )
        for entry in pipe.run():
            print(entry)
    """

    def __init__(
        self,
        path: str,
        highlight_key: str = "_highlights",
    ) -> None:
        self._pipeline = LogPipeline(path)
        self._highlighter = LogHighlighter(highlight_key=highlight_key)

    @property
    def pipeline(self) -> LogPipeline:
        return self._pipeline

    @property
    def highlighter(self) -> LogHighlighter:
        return self._highlighter

    def add_filter(self, f: Any) -> "HighlightPipeline":
        """Delegate filter registration to the inner pipeline."""
        self._pipeline.add_filter(f)
        return self

    def add_rule(
        self, field: str, pattern: str, flags: int = 0
    ) -> "HighlightPipeline":
        """Register a highlight rule."""
        self._highlighter.add_rule(field, pattern, flags)
        return self

    def enrich(self, key: str, value: Any) -> "HighlightPipeline":
        """Add a static enrichment field via the inner pipeline."""
        self._pipeline.enrich(key, value)
        return self

    def run(self) -> List[Dict[str, Any]]:
        """Execute the pipeline and return highlighted entries."""
        entries = self._pipeline.run()
        return list(self._highlighter.stream(entries))
