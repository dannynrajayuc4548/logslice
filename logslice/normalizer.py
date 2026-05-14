"""LogNormalizer — standardise field names and values across log entries."""
from __future__ import annotations

from typing import Any, Callable, Dict, Iterable, Iterator, Optional


class LogNormalizer:
    """Rename fields and coerce values so every entry shares a common shape.

    Example::

        norm = (
            LogNormalizer()
            .alias("lvl", "level")
            .alias("msg", "message")
            .coerce("level", str.upper)
        )
        clean = list(norm.stream(raw_entries))
    """

    def __init__(self) -> None:
        self._aliases: Dict[str, str] = {}   # old_key -> new_key
        self._coercions: Dict[str, Callable[[Any], Any]] = {}

    # ------------------------------------------------------------------
    # builder API
    # ------------------------------------------------------------------

    def alias(self, old_key: str, new_key: str) -> "LogNormalizer":
        """Rename *old_key* to *new_key* in every entry."""
        if not old_key or not old_key.strip():
            raise ValueError("old_key must be a non-empty string")
        if not new_key or not new_key.strip():
            raise ValueError("new_key must be a non-empty string")
        self._aliases[old_key] = new_key
        return self

    def coerce(self, key: str, fn: Callable[[Any], Any]) -> "LogNormalizer":
        """Apply *fn* to the value of *key* (after any aliasing)."""
        if not key or not key.strip():
            raise ValueError("key must be a non-empty string")
        if not callable(fn):
            raise TypeError("fn must be callable")
        self._coercions[key] = fn
        return self

    # ------------------------------------------------------------------
    # processing
    # ------------------------------------------------------------------

    def apply(self, entry: Dict[str, Any]) -> Dict[str, Any]:
        """Return a new dict with aliases and coercions applied."""
        result: Dict[str, Any] = {}
        for k, v in entry.items():
            new_k = self._aliases.get(k, k)
            result[new_k] = v

        for key, fn in self._coercions.items():
            if key in result:
                result[key] = fn(result[key])

        return result

    def stream(
        self, entries: Iterable[Dict[str, Any]]
    ) -> Iterator[Dict[str, Any]]:
        """Yield normalised copies of every entry in *entries*."""
        for entry in entries:
            yield self.apply(entry)

    def collect(
        self, entries: Iterable[Dict[str, Any]]
    ) -> list:
        """Return a list of all normalised entries."""
        return list(self.stream(entries))
