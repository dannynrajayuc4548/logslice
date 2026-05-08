"""LogEnricher: attach computed or static fields to log entries."""

from typing import Any, Callable, Dict, Iterable, Iterator, Optional


class LogEnricher:
    """Attach extra fields to log entries via static values or callables.

    Example::

        enricher = LogEnricher()
        enricher.add("env", "production")
        enricher.add("host", lambda e: socket.gethostname())
        entries = list(enricher.enrich(raw_entries))
    """

    def __init__(self) -> None:
        self._rules: list = []  # list of (key, value_or_callable)

    # ------------------------------------------------------------------
    # Builder API
    # ------------------------------------------------------------------

    def add(self, key: str, value: Any) -> "LogEnricher":
        """Register a static value or a callable(entry) -> value."""
        if not key:
            raise ValueError("key must be a non-empty string")
        self._rules.append((key, value))
        return self

    def remove(self, key: str) -> "LogEnricher":
        """Remove all rules registered under *key*."""
        self._rules = [(k, v) for k, v in self._rules if k != key]
        return self

    # ------------------------------------------------------------------
    # Processing
    # ------------------------------------------------------------------

    def apply(self, entry: Dict[str, Any]) -> Dict[str, Any]:
        """Return a new dict with enrichment fields added."""
        out = dict(entry)
        for key, value in self._rules:
            out[key] = value(entry) if callable(value) else value
        return out

    def enrich(
        self,
        entries: Iterable[Dict[str, Any]],
        skip_errors: bool = False,
    ) -> Iterator[Dict[str, Any]]:
        """Yield enriched copies of every entry in *entries*."""
        for entry in entries:
            try:
                yield self.apply(entry)
            except Exception:
                if not skip_errors:
                    raise
                yield entry

    # ------------------------------------------------------------------
    # Introspection
    # ------------------------------------------------------------------

    @property
    def rule_keys(self) -> list:
        """Ordered list of registered rule keys (may contain duplicates)."""
        return [k for k, _ in self._rules]
