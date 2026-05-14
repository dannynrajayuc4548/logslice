"""LogLabeler — attach a fixed or computed label to every log entry."""
from __future__ import annotations

from typing import Any, Callable, Dict, Iterable, Iterator, Union

_Resolver = Union[str, int, float, bool, None, Callable[[Dict[str, Any]], Any]]


class LogLabeler:
    """Attach one or more labels to every entry that passes through.

    Labels can be static values or callables that receive the entry and
    return a computed value.

    Example::

        labeler = (
            LogLabeler()
            .add("env", "production")
            .add("score", lambda e: len(e.get("message", "")))
        )
        labeled = list(labeler.apply(entries))
    """

    def __init__(self) -> None:
        self._labels: Dict[str, _Resolver] = {}

    # ------------------------------------------------------------------
    # Configuration
    # ------------------------------------------------------------------

    def add(self, key: str, value: _Resolver) -> "LogLabeler":
        """Register *key* with a static *value* or a callable resolver.

        Raises
        ------
        ValueError
            If *key* is empty.
        """
        if not key or not key.strip():
            raise ValueError("Label key must be a non-empty string.")
        self._labels[key] = value
        return self

    def remove(self, key: str) -> "LogLabeler":
        """Remove a previously registered label by *key* (no-op if absent)."""
        self._labels.pop(key, None)
        return self

    @property
    def keys(self) -> list:
        """Return the list of registered label keys in insertion order."""
        return list(self._labels.keys())

    # ------------------------------------------------------------------
    # Processing
    # ------------------------------------------------------------------

    def _apply_one(self, entry: Dict[str, Any]) -> Dict[str, Any]:
        result = dict(entry)
        for key, resolver in self._labels.items():
            result[key] = resolver(entry) if callable(resolver) else resolver
        return result

    def apply(self, entries: Iterable[Dict[str, Any]]) -> Iterator[Dict[str, Any]]:
        """Yield a labeled copy of every entry in *entries*."""
        for entry in entries:
            yield self._apply_one(entry)
