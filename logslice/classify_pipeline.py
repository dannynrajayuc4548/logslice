"""ClassifyPipeline – convenience wrapper combining LogPipeline + LogClassifier."""
from __future__ import annotations

from typing import Any, Callable, Dict, Iterable, Iterator, List, Optional

from logslice.pipeline import LogPipeline
from logslice.classifier import LogClassifier


class ClassifyPipeline:
    """Run a LogPipeline then classify each surviving entry."""

    def __init__(
        self,
        log_path: str,
        category_field: str = "category",
        default: str = "uncategorized",
    ) -> None:
        self._pipeline = LogPipeline(log_path)
        self._classifier = LogClassifier(
            category_field=category_field,
            default=default,
        )

    # ------------------------------------------------------------------
    # Accessors
    # ------------------------------------------------------------------

    @property
    def pipeline(self) -> LogPipeline:
        return self._pipeline

    @property
    def classifier(self) -> LogClassifier:
        return self._classifier

    # ------------------------------------------------------------------
    # Delegating builder methods
    # ------------------------------------------------------------------

    def add_filter(self, f: Any) -> "ClassifyPipeline":
        self._pipeline.add_filter(f)
        return self

    def add_rule(
        self,
        name: str,
        predicate: Callable[[Dict[str, Any]], bool],
    ) -> "ClassifyPipeline":
        self._classifier.add_rule(name, predicate)
        return self

    # ------------------------------------------------------------------
    # Execution
    # ------------------------------------------------------------------

    def run(self) -> Iterator[Dict[str, Any]]:
        """Yield classified entries that pass all pipeline filters."""
        return self._classifier.feed(self._pipeline.run())

    def collect(self) -> List[Dict[str, Any]]:
        """Return all classified entries as a list."""
        return list(self.run())
