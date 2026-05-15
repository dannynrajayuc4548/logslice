"""LogAnnotator – attach structured annotations to log entries based on rules."""
from __future__ import annotations

from typing import Any, Callable, Dict, Iterable, Iterator, List, Tuple


class LogAnnotator:
    """Attach key/value annotations to entries that match a predicate.

    Example::

        annotator = (
            LogAnnotator()
            .add_rule(lambda e: e.get("level") == "ERROR", "needs_review", True)
            .add_rule(lambda e: "timeout" in e.get("message", ""), "category", "timeout")
        )
        results = list(annotator.apply(entries))
    """

    def __init__(self, annotation_key: str = "annotations") -> None:
        if not annotation_key or not annotation_key.strip():
            raise ValueError("annotation_key must be a non-empty string")
        self._annotation_key = annotation_key
        self._rules: List[Tuple[Callable[[Dict[str, Any]], bool], str, Any]] = []

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def annotation_key(self) -> str:
        return self._annotation_key

    @property
    def rules(self) -> List[Tuple[Callable[[Dict[str, Any]], bool], str, Any]]:
        return list(self._rules)

    # ------------------------------------------------------------------
    # Builder API
    # ------------------------------------------------------------------

    def add_rule(
        self,
        predicate: Callable[[Dict[str, Any]], bool],
        key: str,
        value: Any,
    ) -> "LogAnnotator":
        """Register an annotation rule and return *self* for chaining."""
        if not key or not key.strip():
            raise ValueError("Annotation key must be a non-empty string")
        self._rules.append((predicate, key, value))
        return self

    # ------------------------------------------------------------------
    # Processing
    # ------------------------------------------------------------------

    def annotate(self, entry: Dict[str, Any]) -> Dict[str, Any]:
        """Return a copy of *entry* with matching annotations applied."""
        result = dict(entry)
        annotations: Dict[str, Any] = dict(result.get(self._annotation_key) or {})
        for predicate, key, value in self._rules:
            try:
                if predicate(result):
                    annotations[key] = value
            except Exception:
                pass
        result[self._annotation_key] = annotations
        return result

    def apply(self, entries: Iterable[Dict[str, Any]]) -> Iterator[Dict[str, Any]]:
        """Yield annotated copies of every entry in *entries*."""
        for entry in entries:
            yield self.annotate(entry)
