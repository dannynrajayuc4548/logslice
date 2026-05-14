"""LogClassifier – assign a category label to each log entry based on ordered rules."""
from __future__ import annotations

from typing import Any, Callable, Dict, Iterable, Iterator, List, Optional, Tuple


_Rule = Tuple[str, Callable[[Dict[str, Any]], bool]]


class LogClassifier:
    """Classify log entries into named categories using predicate rules.

    Rules are evaluated in insertion order; the first matching rule wins.
    If no rule matches, *default* is used.
    """

    def __init__(
        self,
        category_field: str = "category",
        default: str = "uncategorized",
    ) -> None:
        if not category_field or not category_field.strip():
            raise ValueError("category_field must be a non-empty string")
        self._category_field = category_field
        self._default = default
        self._rules: List[_Rule] = []

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def category_field(self) -> str:
        return self._category_field

    @property
    def default(self) -> str:
        return self._default

    @property
    def rules(self) -> List[str]:
        """Return rule names in insertion order."""
        return [name for name, _ in self._rules]

    # ------------------------------------------------------------------
    # Builder
    # ------------------------------------------------------------------

    def add_rule(self, name: str, predicate: Callable[[Dict[str, Any]], bool]) -> "LogClassifier":
        """Register a named classification rule."""
        if not name or not name.strip():
            raise ValueError("Rule name must be a non-empty string")
        if not callable(predicate):
            raise TypeError("predicate must be callable")
        self._rules.append((name, predicate))
        return self

    # ------------------------------------------------------------------
    # Core
    # ------------------------------------------------------------------

    def classify(self, entry: Dict[str, Any]) -> Dict[str, Any]:
        """Return a copy of *entry* with the category field set."""
        result = dict(entry)
        for name, predicate in self._rules:
            try:
                if predicate(entry):
                    result[self._category_field] = name
                    return result
            except Exception:
                continue
        result[self._category_field] = self._default
        return result

    def feed(self, entries: Iterable[Dict[str, Any]]) -> Iterator[Dict[str, Any]]:
        """Classify each entry in *entries* and yield the enriched copies."""
        for entry in entries:
            yield self.classify(entry)
