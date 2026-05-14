"""LogScorer — assign a numeric relevance score to log entries based on weighted field rules."""
from __future__ import annotations

from typing import Any, Callable, Dict, Iterable, Iterator, List, Optional, Tuple


Rule = Tuple[Callable[[Dict[str, Any]], bool], float]


class LogScorer:
    """Assign a cumulative numeric score to each log entry.

    Rules are (predicate, weight) pairs.  Every predicate that returns
    *True* for an entry adds its weight to that entry's score.  The score
    is stored under *score_field* (default ``"_score"``).
    """

    def __init__(
        self,
        score_field: str = "_score",
        default_score: float = 0.0,
    ) -> None:
        if not score_field:
            raise ValueError("score_field must be a non-empty string")
        self._score_field = score_field
        self._default_score = default_score
        self._rules: List[Rule] = []

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def score_field(self) -> str:
        return self._score_field

    @property
    def default_score(self) -> float:
        return self._default_score

    @property
    def rules(self) -> List[Rule]:
        return list(self._rules)

    # ------------------------------------------------------------------
    # Building
    # ------------------------------------------------------------------

    def add_rule(
        self,
        predicate: Callable[[Dict[str, Any]], bool],
        weight: float,
    ) -> "LogScorer":
        """Register a scoring rule and return *self* for chaining."""
        if not callable(predicate):
            raise TypeError("predicate must be callable")
        self._rules.append((predicate, weight))
        return self

    def field_equals(
        self, field: str, value: Any, weight: float
    ) -> "LogScorer":
        """Convenience: add a rule that matches when *field* equals *value*."""
        return self.add_rule(lambda e, f=field, v=value: e.get(f) == v, weight)

    def field_contains(
        self, field: str, substring: str, weight: float
    ) -> "LogScorer":
        """Convenience: add a rule that matches when *field* contains *substring*."""
        return self.add_rule(
            lambda e, f=field, s=substring: s in str(e.get(f, "")),
            weight,
        )

    # ------------------------------------------------------------------
    # Scoring
    # ------------------------------------------------------------------

    def score(self, entry: Dict[str, Any]) -> Dict[str, Any]:
        """Return a *copy* of *entry* with the score field populated."""
        total = self._default_score
        for predicate, weight in self._rules:
            try:
                if predicate(entry):
                    total += weight
            except Exception:
                pass
        result = dict(entry)
        result[self._score_field] = total
        return result

    def stream(
        self,
        entries: Iterable[Dict[str, Any]],
        threshold: Optional[float] = None,
    ) -> Iterator[Dict[str, Any]]:
        """Yield scored entries, optionally filtered to *score >= threshold*."""
        for entry in entries:
            scored = self.score(entry)
            if threshold is None or scored[self._score_field] >= threshold:
                yield scored
