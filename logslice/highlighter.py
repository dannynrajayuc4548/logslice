"""Highlight fields or patterns in log entries by adding annotation metadata."""
import re
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple


class LogHighlighter:
    """Annotate log entries with highlight markers for matched fields or patterns.

    Each rule adds a ``_highlights`` list to the entry containing dicts with
    ``field``, ``pattern``, and ``match`` keys for every hit.
    """

    _HIGHLIGHT_KEY = "_highlights"

    def __init__(self, highlight_key: str = _HIGHLIGHT_KEY) -> None:
        if not highlight_key or not highlight_key.strip():
            raise ValueError("highlight_key must be a non-empty string")
        self._highlight_key = highlight_key
        self._rules: List[Tuple[str, re.Pattern]] = []

    @property
    def highlight_key(self) -> str:
        return self._highlight_key

    @property
    def rules(self) -> List[Tuple[str, str]]:
        """Return list of (field, pattern_string) tuples."""
        return [(field, pat.pattern) for field, pat in self._rules]

    def add_rule(self, field: str, pattern: str, flags: int = 0) -> "LogHighlighter":
        """Register a highlight rule for *field* matching *pattern*."""
        if not field or not field.strip():
            raise ValueError("field must be a non-empty string")
        if not pattern:
            raise ValueError("pattern must be a non-empty string")
        self._rules.append((field, re.compile(pattern, flags)))
        return self

    def apply(self, entry: Dict[str, Any]) -> Dict[str, Any]:
        """Return a shallow copy of *entry* with highlights injected."""
        result = dict(entry)
        hits: List[Dict[str, Any]] = []
        for field, pat in self._rules:
            value = result.get(field)
            if value is None:
                continue
            text = str(value)
            for m in pat.finditer(text):
                hits.append({"field": field, "pattern": pat.pattern, "match": m.group()})
        if hits:
            result[self._highlight_key] = hits
        return result

    def stream(
        self, entries: Iterable[Dict[str, Any]]
    ) -> Iterable[Dict[str, Any]]:
        """Yield highlighted copies of every entry in *entries*."""
        for entry in entries:
            yield self.apply(entry)
