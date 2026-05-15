"""AnnotatePipeline – combine LogPipeline filtering with LogAnnotator."""
from __future__ import annotations

from typing import Any, Callable, Dict, Iterable, Iterator, List

from .annotator import LogAnnotator
from .pipeline import LogPipeline


class AnnotatePipeline:
    """Convenience wrapper that filters entries then annotates them.

    Example::

        pipeline = (
            AnnotatePipeline("app.log")
            .add_filter(RegexFilter("error"))
            .add_annotation(lambda e: e.get("level") == "ERROR", "urgent", True)
        )
        for entry in pipeline.stream():
            print(entry)
    """

    def __init__(self, path: str, annotation_key: str = "annotations") -> None:
        self._pipeline = LogPipeline(path)
        self._annotator = LogAnnotator(annotation_key=annotation_key)

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def pipeline(self) -> LogPipeline:
        return self._pipeline

    @property
    def annotator(self) -> LogAnnotator:
        return self._annotator

    # ------------------------------------------------------------------
    # Builder API
    # ------------------------------------------------------------------

    def add_filter(self, f: Any) -> "AnnotatePipeline":
        self._pipeline.add_filter(f)
        return self

    def add_annotation(
        self,
        predicate: Callable[[Dict[str, Any]], bool],
        key: str,
        value: Any,
    ) -> "AnnotatePipeline":
        self._annotator.add_rule(predicate, key, value)
        return self

    # ------------------------------------------------------------------
    # Execution
    # ------------------------------------------------------------------

    def stream(self) -> Iterator[Dict[str, Any]]:
        """Yield filtered and annotated entries."""
        return self._annotator.apply(self._pipeline.stream())

    def collect(self) -> List[Dict[str, Any]]:
        """Return all filtered and annotated entries as a list."""
        return list(self.stream())
